from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
from typing import Dict, List
import asyncio

from agent_manager import agent_manager
from models import Message
from config import settings


app = FastAPI(title="Architecture Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_connections: Dict[str, List[str]] = {}  # agent_id -> connection_ids
    
    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = []
        self.agent_connections[agent_id].append(connection_id)
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from agent connections
        for agent_id, connections in self.agent_connections.items():
            if connection_id in connections:
                connections.remove(connection_id)
                if not connections:
                    del self.agent_connections[agent_id]
    
    async def send_personal_message(self, message: str, connection_id: str):
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_text(message)
    
    async def broadcast_to_agent(self, message: str, agent_id: str):
        if agent_id in self.agent_connections:
            for connection_id in self.agent_connections[agent_id]:
                await self.send_personal_message(message, connection_id)


manager = ConnectionManager()


@app.get("/")
async def get_index():
    """Serve the main HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Architecture Agent</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                display: grid;
                grid-template-columns: 300px 1fr;
                gap: 20px;
                height: 90vh;
            }
            .sidebar {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .main-content {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
            }
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
                background: #fafafa;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 8px;
                max-width: 80%;
            }
            .user-message {
                background: #007bff;
                color: white;
                margin-left: auto;
            }
            .agent-message {
                background: #e9ecef;
                color: #333;
            }
            .chat-input {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ddd;
            }
            .chat-input input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-right: 10px;
            }
            .chat-input button {
                padding: 10px 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .chat-input button:hover {
                background: #0056b3;
            }
            .agent-list {
                margin-bottom: 20px;
            }
            .agent-item {
                padding: 10px;
                margin: 5px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                background: #f8f9fa;
            }
            .agent-item:hover {
                background: #e9ecef;
            }
            .agent-item.active {
                background: #007bff;
                color: white;
            }
            .create-agent {
                margin-bottom: 20px;
            }
            .create-agent input {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .create-agent button {
                width: 100%;
                padding: 10px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .create-agent button:hover {
                background: #218838;
            }
            .diagram-container {
                margin-top: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                min-height: 400px;
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 5px;
            }
            .status-idle { background: #28a745; }
            .status-busy { background: #ffc107; }
            .status-error { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                <h2>Agents</h2>
                <div class="create-agent">
                    <input type="text" id="agentName" placeholder="Agent name">
                    <button onclick="createAgent()">Create Agent</button>
                </div>
                <div class="agent-list" id="agentList">
                    <!-- Agents will be loaded here -->
                </div>
            </div>
            <div class="main-content">
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages">
                        <div class="message agent-message">
                            Welcome! Create an agent to start analyzing your architecture.
                        </div>
                    </div>
                    <div class="chat-input">
                        <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
                <div class="diagram-container" id="diagramContainer">
                    <h3>C4 Architecture Diagram</h3>
                    <div id="diagramContent">
                        <!-- Diagrams will be rendered here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentAgentId = null;
            let ws = null;

            // Load agents on page load
            window.onload = function() {
                loadAgents();
            };

            async function loadAgents() {
                try {
                    const response = await fetch('/api/agents');
                    const agents = await response.json();
                    displayAgents(agents);
                } catch (error) {
                    console.error('Error loading agents:', error);
                }
            }

            function displayAgents(agents) {
                const agentList = document.getElementById('agentList');
                agentList.innerHTML = '';
                
                agents.forEach(agent => {
                    const agentItem = document.createElement('div');
                    agentItem.className = 'agent-item';
                    agentItem.innerHTML = `
                        <span class="status-indicator status-${agent.status}"></span>
                        ${agent.name}
                    `;
                    agentItem.onclick = () => selectAgent(agent.id);
                    agentList.appendChild(agentItem);
                });
            }

            async function createAgent() {
                const nameInput = document.getElementById('agentName');
                const name = nameInput.value.trim();
                
                if (!name) {
                    alert('Please enter an agent name');
                    return;
                }

                try {
                    const response = await fetch('/api/agents', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ name: name })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        nameInput.value = '';
                        loadAgents();
                        selectAgent(result.agent_id);
                    } else {
                        alert('Error creating agent');
                    }
                } catch (error) {
                    console.error('Error creating agent:', error);
                    alert('Error creating agent');
                }
            }

            function selectAgent(agentId) {
                currentAgentId = agentId;
                
                // Update UI
                document.querySelectorAll('.agent-item').forEach(item => {
                    item.classList.remove('active');
                });
                event.target.closest('.agent-item').classList.add('active');
                
                // Clear chat
                document.getElementById('chatMessages').innerHTML = '';
                
                // Connect WebSocket
                connectWebSocket(agentId);
            }

            function connectWebSocket(agentId) {
                if (ws) {
                    ws.close();
                }
                
                ws = new WebSocket(`ws://localhost:8000/ws/${agentId}`);
                
                ws.onopen = function() {
                    console.log('WebSocket connected');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    displayMessage(data.message, data.role);
                    
                    if (data.diagram) {
                        displayDiagram(data.diagram);
                    }
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected');
                };
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message || !currentAgentId) return;
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ message: message }));
                    displayMessage(message, 'user');
                    input.value = '';
                }
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }

            function displayMessage(message, role) {
                const chatMessages = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role}-message`;
                messageDiv.textContent = message;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function displayDiagram(diagramData) {
                const diagramContent = document.getElementById('diagramContent');
                
                if (diagramData.type === 'plotly') {
                    // Render Plotly diagram
                    Plotly.newPlot('diagramContent', diagramData.data);
                } else {
                    // Display diagram info
                    diagramContent.innerHTML = `
                        <h4>${diagramData.name}</h4>
                        <p>Level: ${diagramData.level}</p>
                        <p>Elements: ${diagramData.elements?.length || 0}</p>
                    `;
                }
            }
        </script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    return agent_manager.list_agents()


@app.post("/api/agents")
async def create_agent(request: dict):
    """Create new agent"""
    try:
        agent_id = agent_manager.create_agent(request["name"])
        return {"agent_id": agent_id, "name": request["name"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete agent"""
    success = agent_manager.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"message": "Agent deleted"}


@app.get("/api/agents/{agent_id}/context")
async def get_agent_context(agent_id: str):
    """Get agent context"""
    agent = agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.get_context()


@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for chat with agent"""
    connection_id = await manager.connect(websocket, agent_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message with agent
            response = await agent_manager.process_message(agent_id, message_data["message"])
            
            # Send response back
            await manager.send_personal_message(
                json.dumps({
                    "message": response,
                    "role": "assistant"
                }),
                connection_id
            )
            
            # Get current diagram if available
            agent = agent_manager.get_agent(agent_id)
            if agent and agent.context.get("current_diagram"):
                diagram_id = agent.context["current_diagram"]
                diagram = agent.c4_generator.diagrams.get(diagram_id)
                if diagram:
                    # Generate Plotly diagram
                    fig = agent.c4_generator.generate_plotly_diagram(diagram_id)
                    await manager.send_personal_message(
                        json.dumps({
                            "diagram": {
                                "type": "plotly",
                                "data": fig.to_dict(),
                                "name": diagram.name,
                                "level": diagram.level.value,
                                "elements": [e.name for e in diagram.elements]
                            }
                        }),
                        connection_id
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)


@app.get("/api/diagrams/{diagram_id}")
async def get_diagram(diagram_id: str):
    """Get C4 diagram by ID"""
    # This would need to be implemented to find the diagram across all agents
    # For now, return a placeholder
    return {"message": "Diagram endpoint not implemented yet"}


@app.post("/api/diagrams/{diagram_id}/highlight")
async def highlight_diagram_elements(diagram_id: str, element_ids: List[str]):
    """Highlight elements in diagram"""
    # This would need to be implemented
    return {"message": "Highlight endpoint not implemented yet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)