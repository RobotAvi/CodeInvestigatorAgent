import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory

from models import Agent, AgentStatus, Message
from llm_client import LocalLLMClient
from gitlab_client import gitlab_client
from c4_diagram_generator import C4DiagramGenerator
from code_analyzer import CodeAnalyzer
from config import settings


class ArchitectureAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Initialize components
        self.llm_client = LocalLLMClient()
        self.c4_generator = C4DiagramGenerator()
        self.code_analyzer = CodeAnalyzer()
        
        # Memory and context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.context = {
            "repositories": [],
            "current_diagram": None,
            "analysis_results": {},
            "search_history": []
        }
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        self.executor = AgentExecutor(
            agent=self.workflow,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )
    
    def _create_tools(self) -> List[BaseTool]:
        """Create tools for the agent"""
        tools = []
        
        # GitLab tools
        tools.append(GitLabListRepositoriesTool(self))
        tools.append(GitLabAnalyzeRepositoryTool(self))
        tools.append(GitLabSearchCodeTool(self))
        
        # C4 Diagram tools
        tools.append(C4CreateDiagramTool(self))
        tools.append(C4DrillDownTool(self))
        tools.append(C4HighlightElementsTool(self))
        
        # Code analysis tools
        tools.append(CodeAnalysisTool(self))
        tools.append(FindCodeReferencesTool(self))
        
        return tools
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow"""
        workflow = StateGraph(StateType=Dict[str, Any])
        
        # Add nodes
        workflow.add_node("analyze_request", self._analyze_request_node)
        workflow.add_node("execute_tools", ToolNode(self.tools))
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Add edges
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def _analyze_request_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user request and determine required tools"""
        user_message = state.get("messages", [])[-1]
        
        # Use LLM to analyze request and determine tools needed
        analysis_prompt = f"""
        Analyze the following user request and determine what tools are needed:
        
        User request: {user_message.content}
        
        Available tools:
        - gitlab_list_repositories: List GitLab repositories
        - gitlab_analyze_repository: Analyze repository structure
        - gitlab_search_code: Search code in repositories
        - c4_create_diagram: Create C4 architecture diagram
        - c4_drill_down: Navigate to lower C4 levels
        - c4_highlight_elements: Highlight elements in diagram
        - code_analysis: Analyze code structure
        - find_code_references: Find code references
        
        Return a JSON object with:
        - required_tools: List of tool names needed
        - intent: User's intent (architecture_analysis, code_search, diagram_navigation, etc.)
        - priority: High/Medium/Low
        """
        
        analysis_response = self.llm_client.generate(analysis_prompt)
        
        try:
            import json
            analysis = json.loads(analysis_response)
            state["tool_analysis"] = analysis
        except:
            state["tool_analysis"] = {
                "required_tools": [],
                "intent": "general",
                "priority": "medium"
            }
        
        return state
    
    async def _generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final response to user"""
        messages = state.get("messages", [])
        tool_results = state.get("tool_results", [])
        
        # Generate response using LLM
        response_prompt = f"""
        Based on the user request and tool results, generate a comprehensive response.
        
        User request: {messages[-1].content}
        
        Tool results: {tool_results}
        
        Context: {self.context}
        
        Generate a helpful response that:
        1. Addresses the user's request
        2. References relevant tool results
        3. Provides actionable insights
        4. Suggests next steps if appropriate
        """
        
        response = self.llm_client.generate(response_prompt)
        
        # Add response to state
        state["response"] = response
        return state
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        self.status = AgentStatus.BUSY
        self.last_activity = datetime.now()
        
        try:
            # Add message to memory
            self.memory.chat_memory.add_user_message(message)
            
            # Execute workflow
            result = await self.executor.ainvoke({
                "messages": [HumanMessage(content=message)],
                "chat_history": self.memory.chat_memory.messages
            })
            
            response = result.get("response", "I'm sorry, I couldn't process your request.")
            
            # Add response to memory
            self.memory.chat_memory.add_ai_message(response)
            
            self.status = AgentStatus.IDLE
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            return f"Error processing message: {str(e)}"
    
    def get_context(self) -> Dict[str, Any]:
        """Get current agent context"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "context": self.context,
            "repositories": self.context["repositories"],
            "current_diagram": self.context["current_diagram"]
        }
    
    def update_context(self, updates: Dict[str, Any]):
        """Update agent context"""
        self.context.update(updates)
        self.last_activity = datetime.now()


class AgentManager:
    def __init__(self):
        self.agents: Dict[str, ArchitectureAgent] = {}
        self.max_agents = settings.max_agents
    
    def create_agent(self, name: str) -> str:
        """Create new agent"""
        if len(self.agents) >= self.max_agents:
            raise ValueError(f"Maximum number of agents ({self.max_agents}) reached")
        
        agent_id = str(uuid.uuid4())
        agent = ArchitectureAgent(agent_id, name)
        self.agents[agent_id] = agent
        
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[ArchitectureAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "status": agent.status,
                "created_at": agent.created_at,
                "last_activity": agent.last_activity
            }
            for agent_id, agent in self.agents.items()
        ]
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    async def process_message(self, agent_id: str, message: str) -> str:
        """Process message for specific agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        return await agent.process_message(message)


# Tool implementations
class GitLabListRepositoriesTool(BaseTool):
    name = "gitlab_list_repositories"
    description = "List all GitLab repositories"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, query: str = "") -> str:
        try:
            await gitlab_client.connect()
            repositories = await gitlab_client.list_repositories()
            self.agent.context["repositories"] = repositories
            return f"Found {len(repositories)} repositories: {[repo['name'] for repo in repositories]}"
        except Exception as e:
            return f"Error listing repositories: {str(e)}"


class GitLabAnalyzeRepositoryTool(BaseTool):
    name = "gitlab_analyze_repository"
    description = "Analyze repository structure and code"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, repo_id: str) -> str:
        try:
            analysis = await self.agent.code_analyzer.analyze_repository(repo_id)
            self.agent.context["analysis_results"][repo_id] = analysis
            return f"Analysis complete for repository {repo_id}. Found {len(analysis.get('services', []))} services."
        except Exception as e:
            return f"Error analyzing repository: {str(e)}"


class GitLabSearchCodeTool(BaseTool):
    name = "gitlab_search_code"
    description = "Search code in repositories"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, repo_id: str, query: str) -> str:
        try:
            results = await gitlab_client.search_code(repo_id, query)
            return f"Found {len(results)} code matches for '{query}'"
        except Exception as e:
            return f"Error searching code: {str(e)}"


class C4CreateDiagramTool(BaseTool):
    name = "c4_create_diagram"
    description = "Create C4 architecture diagram"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, system_name: str, description: str = "") -> str:
        try:
            diagram = self.agent.c4_generator.create_context_diagram(system_name, description)
            self.agent.context["current_diagram"] = diagram.id
            return f"Created C4 context diagram for {system_name}"
        except Exception as e:
            return f"Error creating diagram: {str(e)}"


class C4DrillDownTool(BaseTool):
    name = "c4_drill_down"
    description = "Navigate to lower C4 levels"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, element_id: str) -> str:
        try:
            diagram = self.agent.c4_generator.drill_down(element_id)
            if diagram:
                self.agent.context["current_diagram"] = diagram.id
                return f"Drilled down to {diagram.name}"
            else:
                return "No lower level available for this element"
        except Exception as e:
            return f"Error drilling down: {str(e)}"


class C4HighlightElementsTool(BaseTool):
    name = "c4_highlight_elements"
    description = "Highlight elements in diagram"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, diagram_id: str, element_ids: str) -> str:
        try:
            element_list = element_ids.split(",")
            result = self.agent.c4_generator.highlight_elements(diagram_id, element_list)
            return f"Highlighted {len(result.get('highlighted_elements', []))} elements"
        except Exception as e:
            return f"Error highlighting elements: {str(e)}"


class CodeAnalysisTool(BaseTool):
    name = "code_analysis"
    description = "Analyze code structure"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, repo_id: str) -> str:
        try:
            analysis = await self.agent.code_analyzer.analyze_repository(repo_id)
            services = self.agent.code_analyzer.extract_service_info(analysis)
            endpoints = self.agent.code_analyzer.extract_api_endpoints(analysis)
            return f"Analysis complete. Found {len(services)} services and {len(endpoints)} endpoints"
        except Exception as e:
            return f"Error analyzing code: {str(e)}"


class FindCodeReferencesTool(BaseTool):
    name = "find_code_references"
    description = "Find code references"
    
    def __init__(self, agent: ArchitectureAgent):
        super().__init__()
        self.agent = agent
    
    async def _arun(self, search_term: str) -> str:
        try:
            references = []
            for repo_id, analysis in self.agent.context["analysis_results"].items():
                repo_refs = self.agent.code_analyzer.find_code_references(analysis, search_term)
                references.extend(repo_refs)
            return f"Found {len(references)} references for '{search_term}'"
        except Exception as e:
            return f"Error finding references: {str(e)}"


# Global agent manager instance
agent_manager = AgentManager()