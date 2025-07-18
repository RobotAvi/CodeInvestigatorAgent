import asyncio
import json
import websockets
from typing import Dict, Any, List, Optional
from config import settings


class GitLabMCPClient:
    def __init__(self):
        self.server_url = settings.mcp_server_url
        self.websocket = None
        self.request_id = 0
        
    async def connect(self):
        """Connect to MCP server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            # Initialize MCP connection
            await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "notifications": {}
                },
                "clientInfo": {
                    "name": "architecture-agent",
                    "version": "1.0.0"
                }
            })
            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server"""
        if not self.websocket:
            raise Exception("Not connected to MCP server")
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        self.request_id += 1
        
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def list_repositories(self) -> List[Dict[str, Any]]:
        """List GitLab repositories"""
        try:
            response = await self._send_request("gitlab/listRepositories", {})
            return response.get("result", {}).get("repositories", [])
        except Exception as e:
            print(f"Error listing repositories: {e}")
            return []
    
    async def get_repository(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """Get repository details"""
        try:
            response = await self._send_request("gitlab/getRepository", {"id": repo_id})
            return response.get("result", {})
        except Exception as e:
            print(f"Error getting repository: {e}")
            return None
    
    async def list_files(self, repo_id: str, path: str = "") -> List[Dict[str, Any]]:
        """List files in repository"""
        try:
            response = await self._send_request("gitlab/listFiles", {
                "repositoryId": repo_id,
                "path": path
            })
            return response.get("result", {}).get("files", [])
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    async def get_file_content(self, repo_id: str, file_path: str) -> Optional[str]:
        """Get file content"""
        try:
            response = await self._send_request("gitlab/getFileContent", {
                "repositoryId": repo_id,
                "path": file_path
            })
            return response.get("result", {}).get("content")
        except Exception as e:
            print(f"Error getting file content: {e}")
            return None
    
    async def search_code(self, repo_id: str, query: str) -> List[Dict[str, Any]]:
        """Search code in repository"""
        try:
            response = await self._send_request("gitlab/searchCode", {
                "repositoryId": repo_id,
                "query": query
            })
            return response.get("result", {}).get("results", [])
        except Exception as e:
            print(f"Error searching code: {e}")
            return []
    
    async def get_commits(self, repo_id: str, branch: str = "main") -> List[Dict[str, Any]]:
        """Get commits for branch"""
        try:
            response = await self._send_request("gitlab/getCommits", {
                "repositoryId": repo_id,
                "branch": branch
            })
            return response.get("result", {}).get("commits", [])
        except Exception as e:
            print(f"Error getting commits: {e}")
            return []
    
    async def clone_repository(self, repo_url: str, local_path: str) -> bool:
        """Clone repository locally"""
        try:
            response = await self._send_request("gitlab/cloneRepository", {
                "url": repo_url,
                "localPath": local_path
            })
            return response.get("result", {}).get("success", False)
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False


# Singleton instance
gitlab_client = GitLabMCPClient()