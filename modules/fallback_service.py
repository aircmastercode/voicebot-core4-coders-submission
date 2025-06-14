#!/usr/bin/env python3
"""
Fallback Service for P2P Lending Voice AI Assistant

This module provides fallback responses to ensure continuity of conversation 
when the NLP pipeline or backend services are unavailable.
"""

import logging
import json
import random
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class FallbackService:
    """
    Provides fallback responses when the main NLP pipeline fails.
    Uses a combination of pre-defined responses and context-aware templates.
    """
    
    def __init__(self):
        """Initialize the fallback service with response templates."""
        logger.info("Initializing fallback service")
        
        # Generic fallback responses
        self.generic_fallbacks = [
            "I'm having trouble connecting to my knowledge base right now. Could you please try again in a moment?",
            "It seems I'm experiencing some technical difficulties. Let me get back to you on that.",
            "I apologize for the inconvenience, but I'm unable to process that request right now. Please try again.",
            "I'm sorry, but I can't access my full capabilities at the moment. Could we try a different question?",
            "I'm temporarily limited in my responses. Let me try to help with a simpler answer."
        ]
        
        # P2P Lending specific fallback responses
        self.p2p_lending_knowledge = {
            "definition": "P2P lending (peer-to-peer lending) connects individual lenders directly with borrowers through online platforms, bypassing traditional banks. Lenders can earn interest on their investments while borrowers may get more favorable rates than from conventional sources.",
            
            "risks": "P2P lending involves several risks, including credit default risk (borrowers failing to repay), platform risk (the platform itself could fail), liquidity risk (difficulty withdrawing funds before loan maturity), and regulatory risk (changing regulations could impact returns).",
            
            "benefits": "P2P lending offers potentially higher returns for investors compared to traditional savings accounts, more favorable rates for borrowers, portfolio diversification, and accessibility for those who might not qualify for traditional bank loans.",
            
            "regulation": "In India, P2P lending platforms are regulated by the Reserve Bank of India (RBI) and must be registered as Non-Banking Financial Companies (NBFC-P2P). This regulation helps protect both lenders and borrowers by ensuring platforms operate transparently."
        }
        
        # Topic detection keywords
        self.topic_keywords = {
            "definition": ["what is", "define", "meaning", "explain", "understand", "basics", "concept"],
            "risks": ["risk", "danger", "safe", "safety", "concern", "problem", "default", "secure"],
            "benefits": ["benefit", "advantage", "return", "profit", "earn", "gain", "pros"],
            "regulation": ["regulation", "regulated", "legal", "law", "rbi", "compliant", "rules"]
        }

    def get_fallback_response(self, user_query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a fallback response based on the user query and conversation history.
        
        Args:
            user_query: The user's question or statement
            conversation_history: List of conversation turns
            
        Returns:
            A contextually appropriate fallback response
        """
        logger.info("Generating fallback response")
        
        # Default to generic fallback if we can't determine anything better
        fallback_response = random.choice(self.generic_fallbacks)
        
        if not user_query:
            return fallback_response
            
        # Try to detect P2P lending related topics
        detected_topic = self._detect_topic(user_query.lower())
        
        if detected_topic:
            fallback_response = self.p2p_lending_knowledge.get(detected_topic, fallback_response)
            fallback_response = f"{fallback_response}\n\nI apologize if this doesn't fully address your question. Our systems are experiencing some temporary limitations."
        
        return fallback_response
    
    def _detect_topic(self, query: str) -> Optional[str]:
        """
        Detect the topic of the query based on keywords.
        
        Args:
            query: The user's query in lowercase
            
        Returns:
            Topic name if detected, None otherwise
        """
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return topic
        return None
    
    def should_use_fallback(self, nlp_data: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if fallback should be used based on NLP data.
        
        Args:
            nlp_data: The NLP data returned from the pipeline
            
        Returns:
            True if fallback should be used, False otherwise
        """
        # If NLP data is None or empty, use fallback
        if not nlp_data:
            return True
            
        # If there's an error status code, use fallback
        if "statusCode" in nlp_data and nlp_data["statusCode"] != 200:
            return True
            
        # If the response is empty, use fallback
        if "response" not in nlp_data and ("body" not in nlp_data or not nlp_data["body"]):
            return True
            
        return False

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fallback = FallbackService()
    
    # Test queries
    test_queries = [
        "What is P2P lending?",
        "Are there risks with P2P lending?",
        "What are the benefits of P2P lending?",
        "Is P2P lending regulated in India?",
        "How do I make pasta?"
    ]
    
    for query in test_queries:
        response = fallback.get_fallback_response(query)
        print(f"Query: {query}")
        print(f"Response: {response}")
        print("-" * 50) 