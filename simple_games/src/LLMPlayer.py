"""
LLM Player with LangGraph-based self-verification and error correction.
"""

from typing import List, TypedDict, Literal
from pydantic import BaseModel, Field, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
import json

from .player import Player, LLMPlayer
from .topics import Message, Topic
from .game_state import GameState

cot_prompt = """You are a strategic game-playing agent. You must provide your response in the following JSON format:
{{
    "chain_of_thought": "Your reasoning here",
    "policy": [0, 1]  // One-hot vector representing your action choice
}}

The policy must be a one-hot vector (exactly one 1, rest 0s) of the correct length."""
class OutputSchema(BaseModel):
    """Schema for LLM player output."""
    chain_of_thought: str | None = Field(default=None, description="Optional reasoning behind the policy selection")
    policy: List[int] = Field(description="One-hot policy vector")

  

no_cot_prompt = """You are a strategic game-playing agent. You must provide your response in the following JSON format:
{{
    "policy": [0, 1]  // One-hot vector representing your action choice
}}

The policy must be a one-hot vector (exactly one 1, rest 0s) of the correct length."""
class OutputSchemaNoCOT(BaseModel):
    """Schema for LLM player output without chain of thought."""
    policy: List[int] = Field(description="One-hot policy vector")



class GraphState(TypedDict):
    """State for the LangGraph workflow."""
    prompt: str
    num_actions: int
    response: dict | None
    error: str | None
    attempt: int
    max_attempts: int



class LangGraphLLMPlayer(LLMPlayer):
    """LLM Player using LangGraph for self-verification and error correction."""
    
    def __init__(
        self, 
        name: str, 
        num_actions: int, 
        model_name: str = "gpt-4o-mini", 
        use_cot: bool = True,
        max_correction_attempts: int = 3
    ):
        super().__init__(name, num_actions, model_name, use_cot)
        self.max_correction_attempts = max_correction_attempts
        
        # Set schema before initializing chains
        self.schema = OutputSchema if self.use_cot else OutputSchemaNoCOT
        # Initialize chains once
        self._init_chains()
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _init_chains(self):
        """Initialize the LLM chains once during initialization."""
        # Initial response chain template

        # Choose the appropriate prompt based on use_cot
        system_prompt = cot_prompt if self.use_cot else no_cot_prompt
        
        self.initial_chain = (
            ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{content}")
            ])
            | self.llm.with_structured_output(self.schema)
        )
        
        # Correction chain template (will be formatted with error context)
        self.correction_template = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human", "{content}")
        ])
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state graph with nodes and edges."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("initial_response", self._initial_response_node)
        workflow.add_node("validate_output", self._validate_output_node)
        workflow.add_node("correct_errors", self._correct_errors_node)
        
        # Set entry point - always start with initial response
        workflow.set_entry_point("initial_response")
        
        # Initial response always goes to validation
        workflow.add_edge("initial_response", "validate_output")
        
        # After validation: either end (valid) or correct errors (invalid)
        workflow.add_conditional_edges(
            "validate_output",
            self._route_after_validation,
            {
                "valid": END,
                "invalid": "correct_errors"
            }
        )
        
        # After correction: either retry validation or give up
        workflow.add_conditional_edges(
            "correct_errors",
            lambda state: "validate_output" if state["attempt"] < state["max_attempts"] else END,
            {
                "validate_output": "validate_output",
                END: END
            }
        )
        
        return workflow.compile()
    
    def _initial_response_node(self, state: GraphState) -> GraphState:
        """Generate initial response from the LLM."""
        try:
            # Call the chain with a properly formatted message
            response = self.initial_chain.invoke({"content": state["prompt"]})
            
            # Convert response to dict if needed
            state["response"] = response.model_dump() if hasattr(response, 'model_dump') else response
            state["error"] = None
            
            # print(f"[{self.name}] Initial response received: {state['response']}")
            
        except Exception as e:
            state["response"] = None
            state["error"] = f"Initial generation error: {str(e)}"
            print(f"[{self.name}] Error in initial response: {state['error']}")
        
        return state
    
    def _validate_output_node(self, state: GraphState) -> GraphState:
        """Validate the output against requirements."""
        response = state["response"]
        num_actions = state["num_actions"]
        
        try:
            # Check if response exists
            if response is None:
                raise ValueError("No response generated")
            
            # Validate using Pydantic
            validated = self.schema(**response)
            
            # Additional validation for one-hot policy
            policy = validated.policy
            
            if len(policy) != num_actions:
                raise ValueError(f"Policy length {len(policy)} does not match num_actions {num_actions}")
            
            if not all(p in [0, 1] for p in policy):
                raise ValueError("Policy must contain only 0s and 1s")
            
            if sum(policy) != 1:
                raise ValueError(f"Policy must be one-hot (sum=1), got sum={sum(policy)}")
            
            # Validation passed
            state["error"] = None
            
        except ValidationError as e:
            state["error"] = f"Validation error: {str(e)}"
            print(f"[{self.name}] Validation failed: {state['error']}")
        except ValueError as e:
            state["error"] = f"Value error: {str(e)}"
            print(f"[{self.name}] Validation failed: {state['error']}")
        except Exception as e:
            state["error"] = f"Unexpected error: {str(e)}"
            print(f"[{self.name}] Validation failed: {state['error']}")
        
        return state
    
    def _correct_errors_node(self, state: GraphState) -> GraphState:
        """Attempt to correct errors in the output."""
        state["attempt"] += 1
        print(f"[{self.name}] Correcting errors (attempt {state['attempt']}/{state['max_attempts']})...")
        
        # Build system prompt with error context
        cot_prompt = f"""You are a strategic game-playing agent. Your previous response had errors.

Error: {state['error']}

Previous response: {json.dumps(state['response'], indent=2)}

Please correct your response. You must provide a valid JSON with:
{{{{
    "chain_of_thought": "Your reasoning here",
    "policy": [0, 1]  // One-hot vector of length {state['num_actions']}
}}}}

Requirements:
- Policy must be exactly {state['num_actions']} elements long
- Policy must be one-hot: exactly one 1, all others 0
- All policy values must be either 0 or 1"""

        no_cot_prompt = f"""You are a strategic game-playing agent. Your previous response had errors.

Error: {state['error']}

Previous response: {json.dumps(state['response'], indent=2)}

Please correct your response. You must provide a valid JSON with:
{{{{
    "policy": [0, 1]  // One-hot vector of length {state['num_actions']}
}}}}

Requirements:
- Policy must be exactly {state['num_actions']} elements long
- Policy must be one-hot: exactly one 1, all others 0
- All policy values must be either 0 or 1"""

        system_prompt = cot_prompt if self.use_cot else no_cot_prompt
        
        try:
            correction_chain = self.correction_template | self.llm.with_structured_output(self.schema)
            response = correction_chain.invoke({
                "system_prompt": system_prompt,
                "content": state["prompt"]
            })
            state["response"] = response.model_dump() if hasattr(response, 'model_dump') else response
            state["error"] = None
        except Exception as e:
            state["error"] = f"Correction error: {str(e)}"
        
        return state
    
    def _route_after_validation(self, state: GraphState) -> Literal["valid", "invalid"]:
        """Route after validation."""
        return "valid" if state["error"] is None else "invalid"
    
    def handle_message(self, message: Message, state: GameState) -> Message:
        """Process incoming message and return policy using LangGraph workflow."""
        # Use parent class's prompt building
        prompt = self._build_prompt(message, state)
        self.prompts_sent.append(prompt)
        
        # Initialize graph state
        graph_state: GraphState = {
            "prompt": prompt,
            "num_actions": self.num_actions,
            "response": None,
            "error": None,
            "attempt": 0,
            "max_attempts": self.max_correction_attempts
        }
        
        # print(f"[{self.name}] Starting LangGraph workflow with prompt: {prompt[:200]}...")
        
        # Run the workflow with self-verification and error correction
        final_state = self.workflow.invoke(graph_state)
        
        # Extract policy from final state
        if final_state["response"] and final_state["error"] is None:
            policy = self._validate_one_hot_policy(final_state["response"].get("policy", [0] * self.num_actions))  # Use parent's validation
            # Safely get chain_of_thought (may be missing when use_cot=False or model didn't provide it)
            chain_of_thought = final_state["response"].get("chain_of_thought")
        else:
            # Fallback to random policy if all attempts failed
            print(f"[{self.name}] All validation attempts failed, using random policy")
            policy = self._validate_one_hot_policy([0] * self.num_actions)  # Use parent's validation for random policy
            chain_of_thought = "Fallback: validation failed after all attempts"
        
        content = {"policy": policy, "player": self.name}
        if self.use_cot:
            content["chain_of_thought"] = chain_of_thought
            
        return Message(
            sender=self.name,
            receiver="moderator",
            topic=Topic("policy"),
            content=content
        )
    

