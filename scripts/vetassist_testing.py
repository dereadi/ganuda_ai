#!/usr/bin/env python3
from crawl4ai import AsyncWebCrawler
import asyncio

async def test_login(email, password):
    async with AsyncWebCrawler() as crawler:
        # Navigate to login
        result = await crawler.arun(
            url="https://vetassist.ganuda.us/login",
            js_code=f''
                document.querySelector('input[name="email"]').value = "{email}";
                document.querySelector('input[name="password"]').value = "{password}";
                document.querySelector('button[type="submit"]').click();
            '',
            wait_for="networkidle"
        )
        return result

# Add more test functions as needed for different scenarios

# Example usage
if __name__ == "__main__":
    # Example test case
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(test_login("test1@vetassist.test", "password1"))
    print(result)
