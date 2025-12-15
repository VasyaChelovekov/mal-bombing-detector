"""
MyAnimeList platform adapter.

Implements the AnimePlatform interface for scraping
data from MyAnimeList.net.
"""

from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from ..core.models import AnimeData, ScoreDistribution
from ..utils.cache import FileCache, get_cache
from ..utils.config import get_config
from ..utils.logging import get_logger
from .base import (
    AnimePlatform,
    NotFoundError,
    PlatformError,
)


logger = get_logger(__name__)


class MyAnimeListPlatform(AnimePlatform):
    """
    MyAnimeList platform adapter.
    
    Scrapes anime data from MyAnimeList.net including:
    - Top anime rankings
    - Score distributions
    - Basic anime information
    
    Implements rate limiting and caching for respectful scraping.
    
    Example:
        >>> async with MyAnimeListPlatform() as mal:
        ...     top = await mal.get_top_anime(50)
        ...     for anime in top:
        ...         stats = await mal.get_anime_stats(anime.mal_id)
    """
    
    BASE_URL = "https://myanimelist.net"
    API_URL = "https://api.myanimelist.net/v2"
    
    def __init__(
        self,
        use_cache: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Initialize the MyAnimeList adapter.
        
        Args:
            use_cache: Whether to use caching.
            session: Optional aiohttp session to reuse.
        """
        self.config = get_config()
        self._session = session
        self._owns_session = session is None
        self._last_request_time = 0.0
        
        # Adaptive delay settings from config
        adaptive = self.config.scraping.adaptive_delay
        self._adaptive_enabled = adaptive.enabled
        self._min_delay = adaptive.min_delay
        self._max_delay = adaptive.max_delay
        self._current_delay = self._min_delay if adaptive.enabled else self.config.scraping.request_delay
        self._success_streak = 0
        self._delay_decrease_threshold = adaptive.success_threshold
        self._decrease_factor = adaptive.decrease_factor
        self._increase_factor = adaptive.increase_factor
        self._rate_limit_factor = adaptive.rate_limit_factor
        
        # Cache
        self._use_cache = use_cache and self.config.cache.enabled
        self._cache: Optional[FileCache] = None
        if self._use_cache:
            self._cache = get_cache("mal_anime")
        
        # Platform config
        self._platform_config = self.config.platforms.get('myanimelist')
        self._user_agent = (
            self._platform_config.user_agent
            if self._platform_config
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    
    @property
    def name(self) -> str:
        return "myanimelist"
    
    @property
    def display_name(self) -> str:
        return "MyAnimeList"
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self._session is None or self._session.closed:
            # Create connector
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.scraping.timeout,
                connect=15,
                sock_read=self.config.scraping.timeout,
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                trust_env=True,  # Use system proxy settings
                headers={
                    'User-Agent': self._user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            )
            self._owns_session = True
        return self._session
    
    async def _rate_limit(self) -> None:
        """
        Apply adaptive rate limiting between requests.
        
        Uses dynamic delay that:
        - Starts at minimum (0.5s)
        - Increases on rate limiting or errors
        - Decreases after consecutive successes
        """
        elapsed = time.time() - self._last_request_time
        
        if elapsed < self._current_delay:
            await asyncio.sleep(self._current_delay - elapsed)
        
        self._last_request_time = time.time()
    
    def _on_request_success(self) -> None:
        """Called after successful request to potentially decrease delay."""
        if not self._adaptive_enabled:
            return
            
        self._success_streak += 1
        
        # Decrease delay after several consecutive successes
        if self._success_streak >= self._delay_decrease_threshold:
            self._current_delay = max(
                self._min_delay,
                self._current_delay * self._decrease_factor
            )
            self._success_streak = 0
            logger.debug(f"Decreased delay to {self._current_delay:.2f}s")
    
    def _on_request_error(self, is_rate_limit: bool = False) -> None:
        """Called after failed request to increase delay."""
        if not self._adaptive_enabled:
            return
            
        self._success_streak = 0
        
        if is_rate_limit:
            # Multiply delay on rate limiting
            self._current_delay = min(self._max_delay, self._current_delay * self._rate_limit_factor)
            logger.info(f"Rate limited! Increased delay to {self._current_delay:.2f}s")
        else:
            # Increase on other errors
            self._current_delay = min(self._max_delay, self._current_delay * self._increase_factor)
            logger.debug(f"Request error. Increased delay to {self._current_delay:.2f}s")
    
    async def _make_request(
        self,
        url: str,
        retries: int = None,
    ) -> str:
        """
        Make an HTTP request with retrying and adaptive delay.
        
        Args:
            url: URL to request.
            retries: Number of retries (default from config).
        
        Returns:
            Response text.
        
        Raises:
            RateLimitError: If rate limited.
            PlatformError: For other errors.
        """
        if retries is None:
            retries = self.config.scraping.max_retries
        
        session = await self._ensure_session()
        
        for attempt in range(retries + 1):
            await self._rate_limit()
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        self._on_request_success()
                        return await response.text()
                    elif response.status == 429:
                        self._on_request_error(is_rate_limit=True)
                        retry_after = int(response.headers.get('Retry-After', 30))
                        logger.warning(f"Rate limited. Waiting {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                    elif response.status == 404:
                        raise NotFoundError(f"Not found: {url}")
                    else:
                        self._on_request_error(is_rate_limit=False)
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                self._on_request_error(is_rate_limit=False)
                logger.warning(f"Timeout for {url} (attempt {attempt + 1}/{retries + 1})")
            except aiohttp.ClientError as e:
                self._on_request_error(is_rate_limit=False)
                logger.warning(f"Request error: {e} (attempt {attempt + 1})")
            
            if attempt < retries:
                await asyncio.sleep(self.config.scraping.retry_delay)
        
        raise PlatformError(f"Failed after {retries + 1} attempts: {url}")
    
    async def get_top_anime(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AnimeData]:
        """Get top-rated anime from MAL."""
        results = []
        
        # MAL shows 50 per page
        items_per_page = 50
        start_page = offset // items_per_page
        pages_needed = (limit + items_per_page - 1) // items_per_page
        
        for page in range(start_page, start_page + pages_needed):
            url = f"{self.BASE_URL}/topanime.php?limit={page * items_per_page}"
            
            try:
                html = await self._make_request(url)
                anime_list = self._parse_top_anime_page(html)
                results.extend(anime_list)
                
                if len(results) >= limit:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching top anime page {page}: {e}")
                break
        
        return results[:limit]
    
    def _parse_top_anime_page(self, html: str) -> List[AnimeData]:
        """Parse the top anime listing page."""
        soup = BeautifulSoup(html, 'lxml')
        results = []
        
        for row in soup.select('tr.ranking-list'):
            try:
                # Rank
                rank_elem = row.select_one('td.rank span')
                rank = int(rank_elem.text.strip()) if rank_elem else 0
                
                # Title and URL
                title_elem = row.select_one('td.title a.hoverinfo_trigger')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                url = title_elem.get('href', '')
                
                # Extract MAL ID from URL
                mal_id_match = re.search(r'/anime/(\d+)', url)
                if not mal_id_match:
                    continue
                mal_id = int(mal_id_match.group(1))
                
                # Score
                score_elem = row.select_one('td.score span')
                score = float(score_elem.text.strip()) if score_elem else 0.0
                
                # Members (optional)
                members_elem = row.select_one('td.members')
                members = 0
                if members_elem:
                    members_text = members_elem.text.strip().replace(',', '')
                    try:
                        members = int(members_text)
                    except ValueError:
                        pass
                
                results.append(AnimeData(
                    mal_id=mal_id,
                    title=title,
                    url=url,
                    rank=rank,
                    score=score,
                    members=members,
                ))
                
            except Exception as e:
                logger.debug(f"Error parsing anime row: {e}")
                continue
        
        return results
    
    async def get_anime_stats(
        self,
        anime_id: int,
    ) -> Optional[AnimeData]:
        """Get detailed stats including score distribution."""
        # Check cache
        cache_key = f"stats_{anime_id}"
        if self._cache and self._cache.has(cache_key):
            cached = self._cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for anime {anime_id}")
                return AnimeData.from_dict(cached)
        
        # Fetch stats page
        url = f"{self.BASE_URL}/anime/{anime_id}/_/stats"
        
        try:
            html = await self._make_request(url)
            anime_data = self._parse_stats_page(html, anime_id)
            
            # Cache the result
            if anime_data and self._cache:
                self._cache.set(cache_key, anime_data.to_dict())
            
            return anime_data
            
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error fetching stats for {anime_id}: {e}")
            raise
    
    def _parse_stats_page(self, html: str, anime_id: int) -> Optional[AnimeData]:
        """Parse the anime stats page."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Get title
        title_elem = soup.select_one('h1.title-name')
        title = title_elem.text.strip() if title_elem else f"Anime {anime_id}"
        
        # Get score - try multiple selectors as page structure varies
        score = 0.0
        # Try span.score-label first (stats page)
        score_elem = soup.select_one('span.score-label')
        if not score_elem:
            # Try div.score-label (main anime page)
            score_elem = soup.select_one('div.score-label')
        if score_elem:
            try:
                score = float(score_elem.text.strip())
            except ValueError:
                pass
        
        # Parse score distribution
        vote_counts: Dict[int, int] = {}
        percentages: Dict[int, float] = {}
        total_votes = 0
        
        score_stats = soup.find('table', class_='score-stats')
        
        if score_stats:
            for row in score_stats.find_all('tr'):
                try:
                    # Get score value
                    score_label = row.find('td', class_=re.compile(r'score-label'))
                    if not score_label:
                        continue
                    score_value = int(score_label.text.strip())
                    
                    # Get vote count from small tag
                    small_elem = row.find('small')
                    if small_elem:
                        match = re.search(r'\((\d+)\s*votes?\)', small_elem.text)
                        if match:
                            votes = int(match.group(1))
                            vote_counts[score_value] = votes
                            total_votes += votes
                            continue
                    
                    # Alternative: parse from span
                    span_elem = row.find('span')
                    if span_elem:
                        match = re.search(r'\((\d+)\s*votes?\)', span_elem.text)
                        if match:
                            votes = int(match.group(1))
                            vote_counts[score_value] = votes
                            total_votes += votes
                            
                except Exception as e:
                    logger.debug(f"Error parsing score row: {e}")
        
        # Calculate percentages
        if total_votes > 0:
            for score_val, count in vote_counts.items():
                percentages[score_val] = round((count / total_votes) * 100, 2)
        
        if not vote_counts:
            return None
        
        # Create distribution
        distribution = ScoreDistribution(
            percentages=percentages,
            vote_counts=vote_counts,
            total_votes=total_votes,
        )
        
        return AnimeData(
            mal_id=anime_id,
            title=title,
            url=f"{self.BASE_URL}/anime/{anime_id}",
            score=score,
            distribution=distribution,
            scraped_at=datetime.now(),
        )
    
    async def get_anime_by_id(
        self,
        anime_id: int,
    ) -> Optional[AnimeData]:
        """Get basic anime info by ID."""
        url = f"{self.BASE_URL}/anime/{anime_id}"
        
        try:
            html = await self._make_request(url)
            return self._parse_anime_page(html, anime_id)
        except NotFoundError:
            return None
    
    def _parse_anime_page(self, html: str, anime_id: int) -> Optional[AnimeData]:
        """Parse basic anime page."""
        soup = BeautifulSoup(html, 'lxml')
        
        title_elem = soup.select_one('h1.title-name')
        title = title_elem.text.strip() if title_elem else ""
        
        score_elem = soup.select_one('div.score-label')
        score = 0.0
        if score_elem:
            try:
                score = float(score_elem.text.strip())
            except ValueError:
                pass
        
        return AnimeData(
            mal_id=anime_id,
            title=title,
            url=f"{self.BASE_URL}/anime/{anime_id}",
            score=score,
        )
    
    async def search_anime(
        self,
        query: str,
        limit: int = 10,
    ) -> List[AnimeData]:
        """Search for anime by title."""
        url = f"{self.BASE_URL}/anime.php?q={query}&cat=anime"
        
        try:
            html = await self._make_request(url)
            return self._parse_search_results(html)[:limit]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _parse_search_results(self, html: str) -> List[AnimeData]:
        """Parse search results page."""
        soup = BeautifulSoup(html, 'lxml')
        results = []
        
        for row in soup.select('div.js-block-list tr'):
            try:
                link = row.select_one('a.hoverinfo_trigger')
                if not link:
                    continue
                
                title = link.text.strip()
                url = link.get('href', '')
                
                mal_id_match = re.search(r'/anime/(\d+)', url)
                if not mal_id_match:
                    continue
                
                results.append(AnimeData(
                    mal_id=int(mal_id_match.group(1)),
                    title=title,
                    url=url,
                ))
            except Exception:
                continue
        
        return results
    
    async def close(self) -> None:
        """Close the session and flush cache."""
        if self._cache:
            self._cache.flush()
        
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
