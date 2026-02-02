class UnifiedSessionManager:
    def __init__(self):
        self.sessions = {}  # Dictionary to store active sessions
        self.event_log = []  # Log of all session events

    def get_or_create(self, session_id, adapter_type):
        """
        Retrieves an existing session or creates a new one based on the session ID and adapter type.
        
        Parameters:
            session_id (str): Unique identifier for the session.
            adapter_type (str): Type of adapter (e.g., 'telegram', 'api', 'web', 'cli', 'jr_agent').
        
        Returns:
            SessionAdapter: The session adapter instance.
        """
        session_key = (session_id, adapter_type)
        if session_key not in self.sessions:
            if adapter_type == 'telegram':
                self.sessions[session_key] = TelegramSessionAdapter(session_id)
            elif adapter_type == 'api':
                self.sessions[session_key] = APISessionAdapter(session_id)
            elif adapter_type == 'web':
                self.sessions[session_key] = WebSessionAdapter(session_id)
            elif adapter_type == 'cli':
                self.sessions[session_key] = CLISessionAdapter(session_id)
            elif adapter_type == 'jr_agent':
                self.sessions[session_key] = JrAgentSessionAdapter(session_id)
            else:
                raise ValueError("Unsupported adapter type")
        return self.sessions[session_key]

    def continue_session(self, session_id, adapter_type, state):
        """
        Continues an existing session by restoring its state.
        
        Parameters:
            session_id (str): Unique identifier for the session.
            adapter_type (str): Type of adapter.
            state (dict): Previous session state to restore.
        """
        session_key = (session_id, adapter_type)
        if session_key in self.sessions:
            self.sessions[session_key].restore_state(state)
        else:
            raise KeyError("Session not found")

    def add_event(self, session_id, adapter_type, event_data):
        """
        Logs an event to the session's event log.
        
        Parameters:
            session_id (str): Unique identifier for the session.
            adapter_type (str): Type of adapter.
            event_data (dict): Details of the event (e.g., user input, system response).
        """
        session_key = (session_id, adapter_type)
        if session_key in self.sessions:
            self.event_log.append({
                'session_id': session_id,
                'adapter_type': adapter_type,
                'event': event_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            raise KeyError("Session not found")

    def get_context(self, session_id, adapter_type):
        """
        Retrieves the current context of a session.
        
        Parameters:
            session_id (str): Unique identifier for the session.
            adapter_type (str): Type of adapter.
        
        Returns:
            dict: Session context (history, events, etc.).
        """
        session_key = (session_id, adapter_type)
        if session_key in self.sessions:
            return self.sessions[session_key].get_context()
        else:
            raise KeyError("Session not found")

    def build_prompt_context(self, session_id, adapter_type, new_input):
        """
        Builds the prompt context for the AI model, applying InfiniPot-style compression if needed.
        
        Parameters:
            session_id (str): Unique identifier for the session.
            adapter_type (str): Type of adapter.
            new_input (str): New user input to include in the prompt.
        
        Returns:
            str: Compressed or uncompressed prompt context.
        """
        session_key = (session_id, adapter_type)
        if session_key not in self.sessions:
            raise KeyError("Session not found")

        context = self.get_context(session_id, adapter_type)
        full_context = context + [new_input]
        
        # Check token count (simplified example; actual implementation would use tokenization)
        token_count = self._estimate_token_count(full_context)
        
        if token_count > 3000:
            # Apply InfiniPot-style compression
            return self._compress_context(full_context)
        else:
            return full_context

    def _estimate_token_count(self, context):
        """
        Estimates the number of tokens in the given context.
        
        Parameters:
            context (list): List of strings representing the context.
        
        Returns:
            int: Estimated token count.
        """
        # Placeholder for actual tokenization logic (e.g., using a tokenizer like tiktoken)
        return sum(len(item) for item in context)  # Simplified for demonstration

    def _compress_context(self, context):
        """
        Applies InfiniPot-style compression to reduce token count.
        
        Parameters:
            context (list): List of strings to compress.
        
        Returns:
            list: Compressed context.
        """
        # Simplified compression logic (replace with actual InfiniPot algorithm)
        compressed = []
        for item in context:
            if len(item) > 100:  # Example threshold
                compressed.append(item[:100] + "...")  # Truncate long items
            else:
                compressed.append(item)
        return compressed
```

---

## Session Adapters  

The UnifiedSessionManager relies on session adapters to handle platform-specific interactions. Each adapter implements the necessary methods to manage sessions, send/receive messages, and interact with the platform’s API. Below are the implementations of each adapter.

### TelegramSessionAdapter  

The `TelegramSessionAdapter` manages sessions for Telegram bots. It handles message reception, session state storage, and event logging.  

```python
class TelegramSessionAdapter:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = []
        self.telegram_bot = None  # Initialize with a Telegram bot instance

    def receive_message(self, message):
        """
        Handles incoming messages from Telegram.
        
        Parameters:
            message (dict): Telegram message data.
        """
        self.context.append(message['text'])
        self.add_event(message)

    def send_message(self, text):
        """
        Sends a message via Telegram.
        
        Parameters:
            text (str): Message to send.
        """
        # Implementation depends on the Telegram bot API
        pass

    def restore_state(self, state):
        """
        Restores the session state from a saved state.
        
        Parameters:
            state (dict): Previous session state.
        """
        self.context = state.get('context', [])
        # Additional state restoration logic

    def get_context(self):
        return self.context
```

### APISessionAdapter  

The `APISessionAdapter` interacts with external APIs. It manages API requests, handles responses, and ensures session continuity.  

```python
class APISessionAdapter:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = []
        self.api_client = None  # Initialize with an API client

    def make_api_call(self, endpoint, data):
        """
        Makes an API call and updates the session context.
        
        Parameters:
            endpoint (str): API endpoint URL.
            data (dict): Data to send in the request.
        """
        # Simulated API call
        response = {"status": "success", "data": data.get('query', '')}
        self.context.append(response['data'])
        self.add_event({'type': 'api_call', 'endpoint': endpoint, 'data': data})

    def restore_state(self, state):
        self.context = state.get('context', [])

    def get_context(self):
        return self.context
```

### WebSessionAdapter  

The `WebSessionAdapter` manages sessions for web-based interactions, such as web forms or browser-based chat interfaces.  

```python
class WebSessionAdapter:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = []
        self.web_driver = None  # Initialize with a web driver (e.g., Selenium)

    def handle_web_event(self, event):
        """
        Handles web events (e.g., form submissions, clicks).
        
        Parameters:
            event (dict): Web event data.
        """
        self.context.append(event)
        self.add_event(event)

    def restore_state(self, state):
        self.context = state.get('context', [])

    def get_context(self):
        return self.context
```

### CLISessionAdapter  

The `CLISessionAdapter` handles command-line interface sessions. It processes user input and maintains the session state in a terminal environment.  

```python
class CLISessionAdapter:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = []

    def process_input(self, user_input):
        """
        Processes user input from the CLI.
        
        Parameters:
            user_input (str): User-provided command or message.
        """
        self.context.append(user_input)
        self.add_event({'type': 'cli_input', 'input': user_input})

    def restore_state(self, state):
        self.context = state.get('context', [])

    def get_context(self):
        return self.context
```

### JrAgentSessionAdapter  

The `JrAgentSessionAdapter` is designed for junior agent systems, which may have limited computational resources. It optimizes session management for efficiency and simplicity.  

```python
class JrAgentSessionAdapter:
    def __init__(self, session_id):
        self.session_id = session_id
        self.context = []

    def add_data(self, data):
        """
        Adds data to the junior agent's session context.
        
        Parameters:
            data (str): Data to store in the session.
        """
        self.context.append(data)
        self.add_event({'type': 'jr_agent_data', 'data': data})

    def restore_state(self, state):
        self.context = state.get('context', [])

    def get_context(self):
        return self.context
```
