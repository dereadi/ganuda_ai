import applescript
from typing import List, Optional

class FaraBrowser:
    def __init__(self, browser: str = "Safari"):
        """
        Initialize the FaraBrowser with the specified browser.
        
        :param browser: The name of the browser to control (default is Safari).
        """
        self.browser = browser
        self.app = applescript.App(browser)

    def open_url(self, url: str) -> None:
        """
        Open a URL in the specified browser.
        
        :param url: The URL to open.
        """
        script = f'tell application "{self.browser}" to open location "{url}"'
        self.app.run(script)

    def close_tab(self, tab_index: int) -> None:
        """
        Close a specific tab in the browser.
        
        :param tab_index: The index of the tab to close (1-based index).
        """
        script = f'tell application "{self.browser}" to close tab {tab_index} of window 1'
        self.app.run(script)

    def get_current_url(self) -> str:
        """
        Get the current URL of the active tab in the browser.
        
        :return: The current URL.
        """
        script = f'tell application "{self.browser}" to return URL of current tab of window 1'
        return self.app.run(script)

    def execute_javascript(self, script: str) -> Optional[str]:
        """
        Execute JavaScript in the current tab of the browser.
        
        :param script: The JavaScript code to execute.
        :return: The result of the JavaScript execution, if any.
        """
        applescript_code = f'tell application "{self.browser}" to do JavaScript "{script}" in current tab of window 1'
        return self.app.run(applescript_code)

    def capture_screenshot(self, filename: str) -> None:
        """
        Capture a screenshot of the current tab and save it to a file.
        
        :param filename: The filename to save the screenshot.
        """
        script = f'tell application "{self.browser}" to tell current tab of window 1 to capture to "{filename}"'
        self.app.run(script)

    def get_page_title(self) -> str:
        """
        Get the title of the current page in the browser.
        
        :return: The title of the current page.
        """
        script = f'tell application "{self.browser}" to return title of current tab of window 1'
        return self.app.run(script)

    def navigate_back(self) -> None:
        """
        Navigate back in the browser history.
        """
        script = f'tell application "{self.browser}" to go back in current tab of window 1'
        self.app.run(script)

    def navigate_forward(self) -> None:
        """
        Navigate forward in the browser history.
        """
        script = f'tell application "{self.browser}" to go forward in current tab of window 1'
        self.app.run(script)

    def reload_page(self) -> None:
        """
        Reload the current page in the browser.
        """
        script = f'tell application "{self.browser}" to reload current tab of window 1'
        self.app.run(script)

    def switch_to_tab(self, tab_index: int) -> None:
        """
        Switch to a specific tab in the browser.
        
        :param tab_index: The index of the tab to switch to (1-based index).
        """
        script = f'tell application "{self.browser}" to set current tab of window 1 to tab {tab_index}'
        self.app.run(script)

    def create_new_tab(self, url: Optional[str] = None) -> None:
        """
        Create a new tab in the browser, optionally opening a URL.
        
        :param url: The URL to open in the new tab (optional).
        """
        if url:
            script = f'tell application "{self.browser}" to tell window 1 to make new tab with properties {{URL:"{url}"}}'
        else:
            script = f'tell application "{self.browser}" to tell window 1 to make new tab'
        self.app.run(script)

    def close_all_tabs_except_first(self) -> None:
        """
        Close all tabs except the first one in the browser.
        """
        script = f'''
        tell application "{self.browser}"
            repeat with i from (count of tabs of window 1) to 2 by -1
                close tab i of window 1
            end repeat
        end tell
        '''
        self.app.run(script)

    def get_all_tab_urls(self) -> List[str]:
        """
        Get a list of URLs for all open tabs in the browser.
        
        :return: A list of URLs.
        """
        script = f'''
        tell application "{self.browser}"
            set tab_urls to {}
            repeat with t in tabs of window 1
                set end of tab_urls to URL of t
            end repeat
            return tab_urls
        end tell
        '''
        return self.app.run(script)

# Example usage
if __name__ == "__main__":
    browser = FaraBrowser()
    browser.open_url("https://www.example.com")
    print(f"Current URL: {browser.get_current_url()}")
    browser.execute_javascript("document.body.style.backgroundColor='red'")
    browser.capture_screenshot("/path/to/screenshot.png")
    print(f"Page Title: {browser.get_page_title()}")
    browser.navigate_back()
    browser.navigate_forward()
    browser.reload_page()
    browser.create_new_tab("https://www.another-example.com")
    browser.close_tab(2)
    browser.close_all_tabs_except_first()
    print(f"All Tab URLs: {browser.get_all_tab_urls()}")