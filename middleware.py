import logging
from litellm.integrations.custom_logger import CustomLogger

logger = logging.getLogger(__name__)

class AnthropicToolsTranslationMiddleware(CustomLogger):
    """
    Middleware to intercept LiteLLM proxy requests and translate Anthropic's 
    proprietary Computer Use tools (bash, text_editor) into standard OpenAI 
    function schemas so that standard LLMs (like NVIDIA NIM / minimax) can understand them.
    """

    async def async_pre_call_hook(
        self,
        user_api_key_dict,
        cache,
        data: dict,
        call_type: str,
    ):
        """Intercepts the payload before it's sent to the upstream provider."""
        
        # We only care about calls that include tools
        if "tools" not in data or not isinstance(data["tools"], list):
            return data
            
        modified_tools = []
        for tool in data["tools"]:
            tool_type = tool.get("type", "")
            
            # 1. Intercept "bash" computer use tools
            if tool_type.startswith("bash_"):
                logger.info(f"[Middleware] Intercepted Anthropic bash tool: {tool_type}. Translating to OpenAI function schema.")
                modified_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "bash"),
                        "description": "Run commands in a bash shell. You must provide the command to execute. The system will execute it and return the stdout/stderr.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "The bash command to execute. Required."
                                },
                                "restart": {
                                    "type": "boolean",
                                    "description": "If true, restarts the bash session before executing the command."
                                }
                            },
                            "required": ["command"]
                        }
                    }
                })
                
            # 2. Intercept "text_editor" computer use tools
            elif tool_type.startswith("text_editor_"):
                logger.info(f"[Middleware] Intercepted Anthropic text_editor tool: {tool_type}. Translating to OpenAI function schema.")
                modified_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.get("name", "str_replace_editor"),
                        "description": "A tool to view, edit, and replace text in files. Commands: 'view' (read file), 'create' (make new file), 'str_replace' (replace exact string), 'insert' (insert at line), 'undo_edit' (undo last edit).",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                                    "description": "The action to perform."
                                },
                                "path": {
                                    "type": "string",
                                    "description": "Absolute path to the file."
                                },
                                "file_text": {
                                    "type": "string",
                                    "description": "Required for 'create'. The contents of the new file."
                                },
                                "old_str": {
                                    "type": "string",
                                    "description": "Required for 'str_replace'. The exact string to be replaced. Must be unique in the file."
                                },
                                "new_str": {
                                    "type": "string",
                                    "description": "Required for 'str_replace'. The new string to replace the old string."
                                },
                                "insert_line": {
                                    "type": "integer",
                                    "description": "Required for 'insert'. The line number where the insert_text will be added."
                                },
                                "insert_text": {
                                    "type": "string",
                                    "description": "Required for 'insert'. The text to insert."
                                },
                                "view_range": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "description": "Optional for 'view'. [start_line, end_line]"
                                }
                            },
                            "required": ["command", "path"]
                        }
                    }
                })
                
            # Keep other tools exactly as they are (standard functions)
            else:
                modified_tools.append(tool)
                
        # Replace the original tools with our modified ones
        data["tools"] = modified_tools
        return data

# Required by LiteLLM to load the custom logger
proxy_handler_instance = AnthropicToolsTranslationMiddleware()
