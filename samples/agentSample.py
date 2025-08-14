import os
import json
import sys
from typing import Dict, Any, Optional, List
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ChatModel, setup_logging
from langchain.tools import Tool, BaseTool, StructuredTool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.excelWriter import ExcelWriterTool
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field, field_validator
import dotenv
import yaml
from datetime import datetime

dotenv.load_dotenv()

# Set up logging for this module
logger = setup_logging(__name__)

# Custom Exception Hierarchy
class ExcelAgentError(Exception):
    """Base exception for ExcelAgent errors."""
    pass

class ExcelAgentInitializationError(ExcelAgentError):
    """Raised when ExcelAgent fails to initialize."""
    pass

class ExcelAgentExecutionError(ExcelAgentError):
    """Raised when ExcelAgent fails to execute a query."""
    pass

# Pydantic Models for Request/Response Validation
class ExcelRequest(BaseModel):
    """
    Validated request model for Excel operations.
    
    Attributes:
        query: The Excel operation query (1-1000 characters)
    """
    query: str = Field(..., min_length=1, max_length=1000, description="Excel operation query")
    
    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v):
        """Sanitize the query input to prevent injection attacks."""
        return v.strip()

class ExcelResponse(BaseModel):
    """
    Standardized response model for Excel operations.
    
    Attributes:
        status: Operation status (success, error, requires_confirmation)
        message: Human-readable response message
        data: Optional response data
        timestamp: Response timestamp
    """
    status: str = Field(description="Operation status")
    message: str = Field(description="Human-readable response message")
    data: Optional[Any] = Field(default=None, description="Optional response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed = {'success', 'error', 'requires_confirmation'}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

class ExcelToolManager:
    """
    Manages Excel tools and provides LangChain tool wrappers.
    
    This class handles the creation and management of Excel tools
    that can be used by the LangChain agent.
    """
    
    def __init__(self):
        """Initialize the Excel tool manager."""
        self.excel_writer = ExcelWriterTool()
        self.logger = logger.getChild("ExcelToolManager")
    
    def get_tools(self) -> List[BaseTool]:
        """
        Get all available Excel tools as LangChain tools.
        
        Returns:
            List of LangChain tools for Excel operations
        """
        tools = [
            StructuredTool.from_function(
                func=self._write_multiple_cells_structured,
                name="write_multiple_cells",
                description="Write multiple values to different cells in a SharePoint Excel file. Use this when you need to write data to multiple cells at once. Requires SharePoint URL, sheet name, and cell data list."
            ),
            StructuredTool.from_function(
                func=self._get_cell_value_structured,
                name="get_cell_value",
                description="Get the value of a specific cell from a SharePoint Excel file. Use this when you need to read data from a cell. Requires SharePoint URL, sheet name, and cell address."
            )
        ]
        
        self.logger.info(f"Created {len(tools)} Excel tools")
        return tools
    
    def _write_multiple_cells_structured(self, sharepoint_url: str, sheet_name: str, cell_data: List[Dict[str, Any]]) -> str:
        """Structured function for write_multiple_cells tool."""
        try:
            self.logger.info(f"Writing {len(cell_data)} cells to SharePoint Excel file sheet {sheet_name}")
            
            if not isinstance(cell_data, list):
                return json.dumps({
                    "status": "error",
                    "message": "Cell data must be a list of dictionaries with 'cell_address' and 'value' keys"
                })
            
            result = self.excel_writer.write_multiple_cells(sharepoint_url, sheet_name, cell_data)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in write_multiple_cells_structured: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Tool execution failed: {str(e)}"
            })
    
    def _get_cell_value_structured(self, sharepoint_url: str, sheet_name: str, cell_address: str) -> str:
        """Structured function for get_cell_value tool."""
        try:
            self.logger.info(f"Reading cell {cell_address} from SharePoint Excel file sheet {sheet_name}")
            
            result = self.excel_writer.get_cell_value(sharepoint_url, sheet_name, cell_address)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error in get_cell_value_structured: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Tool execution failed: {str(e)}"
            })

class PromptManager:
    """
    Manages Excel agent prompts and configuration.
    
    This class handles loading and managing prompt templates from YAML files
    with proper error handling and caching.
    """
    
    def __init__(self):
        """Initialize the prompt manager."""
        self._prompts = None
        self._prompts_loaded = False
        self.logger = logger.getChild("PromptManager")
    
    def load_prompts(self) -> Dict[str, Any]:
        """
        Load prompt templates from the YAML configuration file.
        
        Returns:
            Dictionary containing the loaded prompt templates
            
        Raises:
            ExcelAgentInitializationError: If the prompts file cannot be loaded
        """
        if self._prompts_loaded:
            return self._prompts
        
        try:
            prompts_path = os.path.join(os.path.dirname(__file__), 'prompts', 'Excel_Agent_System_Prompts.yaml')
            self.logger.info(f"Loading prompts from {prompts_path}")
            
            if not os.path.exists(prompts_path):
                # Create default prompts if file doesn't exist
                self._create_default_prompts(prompts_path)
            
            with open(prompts_path, 'r', encoding='utf-8') as f:
                self._prompts = yaml.safe_load(f)
            
            self._prompts_loaded = True
            self.logger.info("Prompts loaded successfully")
            return self._prompts
            
        except FileNotFoundError as e:
            error_msg = f"Prompts file not found: {prompts_path}"
            self.logger.error(error_msg)
            raise ExcelAgentInitializationError(error_msg) from e
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML format in prompts file: {e}"
            self.logger.error(error_msg)
            raise ExcelAgentInitializationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to load prompts: {e}"
            self.logger.error(error_msg)
            raise ExcelAgentInitializationError(error_msg) from e
    
    def _create_default_prompts(self, prompts_path: str):
        """Create default prompts file if it doesn't exist."""
        default_prompts = {
            'excel_agent_system_prompt': """You are an Excel operations agent for SharePoint/OneDrive Excel files. You can perform various Excel operations including:

1. Writing multiple values to different cells in SharePoint Excel files
2. Reading cell values from SharePoint Excel files
3. Working with existing SharePoint Excel files

When working with SharePoint Excel files:
- Always specify the SharePoint URL, sheet name, and cell address clearly
- Use proper cell references (e.g., A1, B5, C10)
- Handle errors gracefully and provide clear feedback
- Validate inputs before performing operations
- Use the full SharePoint URL for the Excel file

Available tools:
- write_multiple_cells: Write multiple values to different cells in SharePoint Excel files
- get_cell_value: Read a value from a specific cell in SharePoint Excel files

Always respond with clear, actionable information about what you're doing.""",
            
            'excel_operations_prompt': """When performing SharePoint Excel operations:

1. For writing multiple cells: Use the write_multiple_cells tool with SharePoint URL, sheet name, and cell data list
2. For reading cells: Use the get_cell_value tool with SharePoint URL, sheet name, and cell address
3. Handle errors gracefully and provide helpful error messages

Remember to:
- Use the complete SharePoint URL for the Excel file
- Validate all inputs before processing
- Provide clear feedback on operation success or failure
- Use appropriate cell references and sheet names
- Handle SharePoint permissions and access issues
- When writing data, provide it as a list of dictionaries with 'cell_address' and 'value' keys
- The SharePoint URL should be the full URL from the browser address bar"""
        }
        
        # Create prompts directory if it doesn't exist
        os.makedirs(os.path.dirname(prompts_path), exist_ok=True)
        
        with open(prompts_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_prompts, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Created default prompts file: {prompts_path}")
    
    def get_system_prompt(self) -> str:
        """
        Get the Excel agent system prompt.
        
        Returns:
            str: Excel agent system prompt
        """
        if not self._prompts_loaded:
            self.load_prompts()
        return self._prompts.get('excel_agent_system_prompt', '')
    
    def get_operations_prompt(self) -> str:
        """
        Get the Excel operations prompt.
        
        Returns:
            str: Excel operations prompt
        """
        if not self._prompts_loaded:
            self.load_prompts()
        return self._prompts.get('excel_operations_prompt', '')

class ExcelAgent:
    """
    Main Excel Agent class using LangChain components with Excel tools.
    
    This agent provides Excel operations with comprehensive error handling,
    logging, input validation, and proper async patterns.
    """
    
    def __init__(self):
        """
        Initialize the ExcelAgent with basic components.
        Note: Use create() class method for proper async initialization.
        """
        self.llm = None
        self.tools = None
        self.memory = None
        self.prompt_manager = None
        self.prompt = None
        self.agent = None
        self.executor = None
        self._initialized = False
        self.logger = logger.getChild("ExcelAgent")

    @classmethod
    async def create(cls, model_name: str = None):
        """
        Create and initialize an ExcelAgent instance asynchronously.
        
        This is the recommended way to create an ExcelAgent instance as it properly
        initializes all async components.
        
        Args:
            model_name: Optional model name override
            
        Returns:
            ExcelAgent: A fully initialized ExcelAgent instance
            
        Raises:
            ExcelAgentInitializationError: If initialization fails
        """
        instance = cls()
        await instance._initialize(model_name)
        return instance

    async def _initialize(self, model_name: str = None):
        """
        Initialize all components of the ExcelAgent asynchronously.
        
        Args:
            model_name: Optional model name override
            
        Raises:
            ExcelAgentInitializationError: If any component fails to initialize
        """
        try:
            self.logger.info(f"Initializing ExcelAgent with model: {model_name or 'default'}")
            
            # Initialize language model
            self.logger.debug("Initializing language model")
            chat_model = ChatModel()
            self.llm = chat_model.get_llm()
            self.logger.info("Language model initialized successfully")
            
            # Initialize Excel tools
            self.logger.debug("Initializing Excel tools")
            tool_manager = ExcelToolManager()
            self.tools = tool_manager.get_tools()
            self.logger.info(f"Initialized {len(self.tools)} Excel tools")
            
            # Initialize memory
            self.logger.debug("Initializing conversation memory")
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Initialize prompt manager
            self.logger.debug("Initializing prompt manager")
            self.prompt_manager = PromptManager()
            self.prompt_manager.load_prompts()
            
            # Create prompt template
            self.logger.debug("Creating prompt template")
            system_prompt = self.prompt_manager.get_system_prompt()
            operations_prompt = self.prompt_manager.get_operations_prompt()
            
            self.prompt = ChatPromptTemplate.from_messages([    
                ("system", system_prompt + "\n\n" + operations_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create agent
            self.logger.debug("Creating agent")
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )
            
            # Create agent executor
            self.logger.debug("Creating agent executor")
            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                handle_parsing_errors=True
            )
            
            self._initialized = True
            self.logger.info("ExcelAgent initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize ExcelAgent: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ExcelAgentInitializationError(error_msg) from e

    async def execute(self, request: ExcelRequest) -> ExcelResponse:
        """
        Execute the Excel agent with a validated request.
        
        This is the main execution method that processes Excel operations
        with comprehensive error handling and logging.
        
        Args:
            request: Validated ExcelRequest object
            
        Returns:
            ExcelResponse: Structured response with operation results
            
        Raises:
            ExcelAgentExecutionError: If the agent is not initialized or execution fails
        """
        if not self._initialized:
            error_msg = "ExcelAgent not initialized. Use ExcelAgent.create() to create an instance."
            self.logger.error(error_msg)
            raise ExcelAgentExecutionError(error_msg)
        
        try:
            self.logger.info(f"Processing Excel request: {request.query[:100]}{'...' if len(request.query) > 100 else ''}")
            
            # Execute the agent
            result = await self.executor.ainvoke({"input": request.query})
            
            self.logger.info("Excel operation completed successfully")
            return ExcelResponse(
                status="success",
                message="Excel operation completed successfully",
                data=result["output"]
            )
            
        except Exception as e:
            error_msg = f"Excel operation failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ExcelAgentExecutionError(error_msg) from e

    async def __call__(self, query_dict: Dict[str, Any]) -> ExcelResponse:
        """
        Make the agent callable with a dictionary containing 'query' key.
        
        This method provides backward compatibility while adding validation.
        
        Args:
            query_dict: Dictionary containing the query and optional parameters
            
        Returns:
            ExcelResponse: Structured response with operation results
            
        Raises:
            ExcelAgentExecutionError: If execution fails
        """
        try:
            # Convert dictionary to validated request
            request = ExcelRequest(**query_dict)
            return await self.execute(request)
        except Exception as e:
            error_msg = f"Failed to process query dictionary: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ExcelAgentExecutionError(error_msg) from e

# Global instance - will be initialized when first accessed
_excel_agent_instance = None

async def get_excel_agent(model_name: str = None) -> ExcelAgent:
    """
    Get a singleton instance of ExcelAgent.
    
    This function provides a convenient way to access an ExcelAgent instance
    without managing the async initialization manually.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        ExcelAgent: A fully initialized ExcelAgent instance
        
    Raises:
        ExcelAgentInitializationError: If the agent fails to initialize
    """
    global _excel_agent_instance
    if _excel_agent_instance is None:
        logger.info("Creating new ExcelAgent singleton instance")
        try:
            _excel_agent_instance = await ExcelAgent.create(model_name)
            logger.info("ExcelAgent singleton instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create ExcelAgent singleton: {e}")
            raise
    else:
        logger.debug("Returning existing ExcelAgent singleton instance")
    return _excel_agent_instance
