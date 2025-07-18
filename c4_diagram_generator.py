import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from models import C4Element, C4Diagram, C4Level


class C4DiagramGenerator:
    def __init__(self):
        self.diagrams = {}
        self.elements = {}
        
    def create_context_diagram(self, system_name: str, description: str = "") -> C4Diagram:
        """Create C4 Context diagram"""
        diagram_id = str(uuid.uuid4())
        
        # Create main system element
        system_element = C4Element(
            id=f"{diagram_id}_system",
            name=system_name,
            type="System",
            level=C4Level.CONTEXT,
            description=description,
            technology="",
            relationships=[],
            properties={},
            children=[]
        )
        
        diagram = C4Diagram(
            id=diagram_id,
            name=f"{system_name} - Context",
            level=C4Level.CONTEXT,
            elements=[system_element],
            relationships=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.diagrams[diagram_id] = diagram
        self.elements[system_element.id] = system_element
        
        return diagram
    
    def create_container_diagram(self, system_id: str, containers: List[Dict[str, Any]]) -> C4Diagram:
        """Create C4 Container diagram"""
        diagram_id = str(uuid.uuid4())
        
        # Get system element
        system_element = self.elements.get(system_id)
        if not system_element:
            raise ValueError(f"System element {system_id} not found")
        
        elements = [system_element]
        relationships = []
        
        # Create container elements
        for container_info in containers:
            container_id = str(uuid.uuid4())
            container_element = C4Element(
                id=container_id,
                name=container_info["name"],
                type="Container",
                level=C4Level.CONTAINER,
                description=container_info.get("description", ""),
                technology=container_info.get("technology", ""),
                relationships=[],
                properties=container_info.get("properties", {}),
                parent_id=system_id,
                children=[]
            )
            
            elements.append(container_element)
            self.elements[container_id] = container_element
            
            # Add relationship to system
            relationship = {
                "id": str(uuid.uuid4()),
                "from": container_id,
                "to": system_id,
                "description": "deployed on",
                "technology": ""
            }
            relationships.append(relationship)
            
            # Update system children
            system_element.children.append(container_id)
        
        diagram = C4Diagram(
            id=diagram_id,
            name=f"{system_element.name} - Containers",
            level=C4Level.CONTAINER,
            elements=elements,
            relationships=relationships,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.diagrams[diagram_id] = diagram
        return diagram
    
    def create_component_diagram(self, container_id: str, components: List[Dict[str, Any]]) -> C4Diagram:
        """Create C4 Component diagram"""
        diagram_id = str(uuid.uuid4())
        
        # Get container element
        container_element = self.elements.get(container_id)
        if not container_element:
            raise ValueError(f"Container element {container_id} not found")
        
        elements = [container_element]
        relationships = []
        
        # Create component elements
        for component_info in components:
            component_id = str(uuid.uuid4())
            component_element = C4Element(
                id=component_id,
                name=component_info["name"],
                type="Component",
                level=C4Level.COMPONENT,
                description=component_info.get("description", ""),
                technology=component_info.get("technology", ""),
                relationships=[],
                properties=component_info.get("properties", {}),
                parent_id=container_id,
                children=[]
            )
            
            elements.append(component_element)
            self.elements[component_id] = component_element
            
            # Add relationship to container
            relationship = {
                "id": str(uuid.uuid4()),
                "from": component_id,
                "to": container_id,
                "description": "part of",
                "technology": ""
            }
            relationships.append(relationship)
            
            # Update container children
            container_element.children.append(component_id)
        
        diagram = C4Diagram(
            id=diagram_id,
            name=f"{container_element.name} - Components",
            level=C4Level.COMPONENT,
            elements=elements,
            relationships=relationships,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.diagrams[diagram_id] = diagram
        return diagram
    
    def add_relationship(self, diagram_id: str, from_element: str, to_element: str, 
                        description: str, technology: str = "") -> bool:
        """Add relationship between elements"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return False
        
        relationship = {
            "id": str(uuid.uuid4()),
            "from": from_element,
            "to": to_element,
            "description": description,
            "technology": technology
        }
        
        diagram.relationships.append(relationship)
        diagram.updated_at = datetime.now()
        return True
    
    def highlight_elements(self, diagram_id: str, element_ids: List[str]) -> Dict[str, Any]:
        """Highlight specific elements in diagram"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return {}
        
        highlighted_elements = []
        for element in diagram.elements:
            if element.id in element_ids:
                highlighted_elements.append({
                    "id": element.id,
                    "name": element.name,
                    "type": element.type,
                    "highlighted": True
                })
        
        return {
            "diagram_id": diagram_id,
            "highlighted_elements": highlighted_elements
        }
    
    def generate_plotly_diagram(self, diagram_id: str, highlighted_elements: List[str] = None) -> go.Figure:
        """Generate interactive Plotly diagram"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return go.Figure()
        
        # Create nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        # Position elements in a circle
        import math
        num_elements = len(diagram.elements)
        for i, element in enumerate(diagram.elements):
            angle = 2 * math.pi * i / num_elements
            radius = 3
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{element.name}<br>{element.type}")
            
            # Color based on highlighting
            if highlighted_elements and element.id in highlighted_elements:
                node_colors.append("red")
                node_sizes.append(30)
            else:
                node_colors.append("lightblue")
                node_sizes.append(20)
        
        # Create edges
        edge_x = []
        edge_y = []
        edge_text = []
        
        for rel in diagram.relationships:
            from_element = next((e for e in diagram.elements if e.id == rel["from"]), None)
            to_element = next((e for e in diagram.elements if e.id == rel["to"]), None)
            
            if from_element and to_element:
                from_idx = diagram.elements.index(from_element)
                to_idx = diagram.elements.index(to_element)
                
                edge_x.extend([node_x[from_idx], node_x[to_idx], None])
                edge_y.extend([node_y[from_idx], node_y[to_idx], None])
                edge_text.append(rel["description"])
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=2, color='gray'),
                hoverinfo='text',
                text=edge_text,
                showlegend=False
            ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='black')
            ),
            text=node_text,
            textposition="bottom center",
            hoverinfo='text',
            showlegend=False
        ))
        
        fig.update_layout(
            title=f"{diagram.name}",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            width=800,
            height=600
        )
        
        return fig
    
    def get_diagram_hierarchy(self, diagram_id: str) -> Dict[str, Any]:
        """Get diagram hierarchy for navigation"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return {}
        
        hierarchy = {
            "diagram_id": diagram_id,
            "name": diagram.name,
            "level": diagram.level,
            "elements": []
        }
        
        for element in diagram.elements:
            element_info = {
                "id": element.id,
                "name": element.name,
                "type": element.type,
                "level": element.level,
                "has_children": len(element.children) > 0,
                "children": element.children
            }
            hierarchy["elements"].append(element_info)
        
        return hierarchy
    
    def drill_down(self, element_id: str) -> Optional[C4Diagram]:
        """Drill down to next level for an element"""
        element = self.elements.get(element_id)
        if not element or not element.children:
            return None
        
        # Find existing diagram for this element
        for diagram in self.diagrams.values():
            if diagram.elements and diagram.elements[0].id == element_id:
                return diagram
        
        # Create new diagram for children
        child_elements = [self.elements[child_id] for child_id in element.children 
                         if child_id in self.elements]
        
        if not child_elements:
            return None
        
        diagram = C4Diagram(
            id=str(uuid.uuid4()),
            name=f"{element.name} - Details",
            level=self._get_next_level(element.level),
            elements=[element] + child_elements,
            relationships=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.diagrams[diagram.id] = diagram
        return diagram
    
    def _get_next_level(self, current_level: C4Level) -> C4Level:
        """Get next C4 level"""
        level_order = [C4Level.CONTEXT, C4Level.CONTAINER, C4Level.COMPONENT, C4Level.CODE]
        try:
            current_index = level_order.index(current_level)
            if current_index < len(level_order) - 1:
                return level_order[current_index + 1]
        except ValueError:
            pass
        return current_level
    
    def export_diagram(self, diagram_id: str, format: str = "json") -> str:
        """Export diagram in specified format"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return ""
        
        if format == "json":
            return diagram.model_dump_json()
        elif format == "dot":
            return self._generate_dot_format(diagram)
        else:
            return diagram.model_dump_json()
    
    def _generate_dot_format(self, diagram: C4Diagram) -> str:
        """Generate DOT format for Graphviz"""
        dot_lines = ["digraph G {"]
        dot_lines.append("  rankdir=TB;")
        dot_lines.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        
        # Add nodes
        for element in diagram.elements:
            dot_lines.append(f'  "{element.id}" [label="{element.name}\\n{element.type}"];')
        
        # Add edges
        for rel in diagram.relationships:
            dot_lines.append(f'  "{rel["from"]}" -> "{rel["to"]}" [label="{rel["description"]}"];')
        
        dot_lines.append("}")
        return "\n".join(dot_lines)