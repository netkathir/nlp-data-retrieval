"""
Response Generator Module
Formats and summarizes search results using GPT
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI


class ResponseGenerator:
    """Generate natural language responses and summaries"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize ResponseGenerator
        
        Args:
            api_key: OpenAI API key
            model: Chat model name
        """
        from config import OPENAI_API_KEY, CHAT_MODEL, OPENAI_API_BASE
        
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or CHAT_MODEL
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        if OPENAI_API_BASE:
            self.client = OpenAI(api_key=self.api_key, base_url=OPENAI_API_BASE)
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def format_results(self, results: List[Dict[str, Any]], 
                      format_type: str = "detailed") -> str:
        """
        Format search results for display
        
        Args:
            results: List of vendor records
            format_type: "detailed", "brief", or "table"
            
        Returns:
            Formatted string
        """
        if not results:
            return "No matching vendors found."
        
        if format_type == "brief":
            return self._format_brief(results)
        elif format_type == "table":
            return self._format_table(results)
        else:
            return self._format_detailed(results)
    
    def _format_detailed(self, results: List[Dict[str, Any]]) -> str:
        """Format results with full details"""
        from utils.text_processor import TextProcessor
        
        output = []
        output.append(f"Found {len(results)} matching vendor(s):\n")
        
        for idx, vendor in enumerate(results, 1):
            score = vendor.get('similarity_score', 0)
            output.append(f"\n{'='*60}")
            output.append(f"Result #{idx} - Match Score: {score:.2%}\n")
            output.append(TextProcessor.format_for_display(vendor))
        
        output.append(f"\n{'='*60}")
        return "\n".join(output)
    
    def _format_brief(self, results: List[Dict[str, Any]]) -> str:
        """Format results briefly using field index configuration"""
        try:
            from config import FIELD_MAP, BRIEF_DISPLAY_INDICES
            
            output = []
            output.append(f"Found {len(results)} vendor(s):\n")
            
            for idx, vendor in enumerate(results, 1):
                # Build brief string using configured display indices
                parts = []
                for field_idx in BRIEF_DISPLAY_INDICES:
                    if field_idx in FIELD_MAP:
                        field_name = FIELD_MAP[field_idx]["name"]
                        value = vendor.get(field_name) or vendor.get(f"field_{field_idx}")
                        if value:
                            parts.append(str(value))
                
                brief_text = " - ".join(parts) if parts else "N/A"
                score = vendor.get('similarity_score', 0)
                output.append(f"{idx}. {brief_text} ({score:.1%} match)")
            
            return "\n".join(output)
            
        except ImportError:
            # Fallback to legacy method
            from config import PRIMARY_DISPLAY_FIELD, FILTER_FIELD_NAMES
            
            output = []
            output.append(f"Found {len(results)} vendor(s):\n")
            
            city_field = FILTER_FIELD_NAMES.get('city', 'vendor_city')
            state_field = FILTER_FIELD_NAMES.get('state', 'vendor_state')
            
            for idx, vendor in enumerate(results, 1):
                name = vendor.get(PRIMARY_DISPLAY_FIELD, 'N/A')
                location = f"{vendor.get(city_field, 'N/A')}, {vendor.get(state_field, 'N/A')}"
                score = vendor.get('similarity_score', 0)
                output.append(f"{idx}. {name} ({location}) - {score:.1%} match")
            
            return "\n".join(output)
    
    def _format_table(self, results: List[Dict[str, Any]]) -> str:
        """Format results as a table using field index configuration"""
        try:
            from config import FIELD_MAP, TABLE_COLUMN_INDICES
            
            output = []
            
            # Build header from configured table columns
            header_parts = ["#"]
            for field_idx in TABLE_COLUMN_INDICES:
                if field_idx in FIELD_MAP:
                    header_parts.append(FIELD_MAP[field_idx]["label"][:20])
            header_parts.append("Match")
            
            output.append(" | ".join(f"{h:<20}" for h in header_parts))
            output.append("-" * (23 * len(header_parts)))
            
            # Build rows
            for idx, vendor in enumerate(results, 1):
                row_parts = [f"{idx}"]
                for field_idx in TABLE_COLUMN_INDICES:
                    if field_idx in FIELD_MAP:
                        field_name = FIELD_MAP[field_idx]["name"]
                        value = vendor.get(field_name) or vendor.get(f"field_{field_idx}") or "N/A"
                        row_parts.append(str(value)[:20])
                
                score = vendor.get('similarity_score', 0)
                row_parts.append(f"{score:.1%}")
                
                output.append(" | ".join(f"{p:<20}" for p in row_parts))
            
            return "\n".join(output)
            
        except ImportError:
            # Fallback to legacy method
            from config import PRIMARY_DISPLAY_FIELD, FILTER_FIELD_NAMES, VENDOR_FIELDS
            
            output = []
            
            city_field = FILTER_FIELD_NAMES.get('city', 'vendor_city')
            state_field = FILTER_FIELD_NAMES.get('state', 'vendor_state')
            
            # Try to find a vehicle/type field from VENDOR_FIELDS
            vehicle_field = None
            for field in VENDOR_FIELDS:
                if 'vehicle' in field.lower() or 'type' in field.lower():
                    vehicle_field = field
                    break
            vehicle_field = vehicle_field or 'vehicle_type'
            
            # Header
            output.append(f"{'#':<3} {'Name':<30} {'Location':<25} {'Type':<20} {'Match':<8}")
            output.append("-" * 90)
            
            # Rows
            for idx, vendor in enumerate(results, 1):
                name = vendor.get(PRIMARY_DISPLAY_FIELD, 'N/A')[:28]
                city = vendor.get(city_field, 'N/A')
                state = vendor.get(state_field, 'N/A')
                location = f"{city}, {state}"[:23]
                vehicle = vendor.get(vehicle_field, 'N/A')[:18]
                score = vendor.get('similarity_score', 0)
                
                output.append(f"{idx:<3} {name:<30} {location:<25} {vehicle:<20} {score:.1%}")
            
            return "\n".join(output)
    
    def generate_summary(self, results: List[Dict[str, Any]], 
                        query: str) -> str:
        """
        Generate a natural language summary of results using GPT with configurable prompts
        
        Args:
            results: Search results
            query: Original user query
            
        Returns:
            Natural language summary
        """
        try:
            from config import AI_SUMMARY_CONFIG, FIELD_MAP
            
            if not results:
                return AI_SUMMARY_CONFIG.get("no_results_message", "No vendors were found matching your query.")
            
            # Limit results for token efficiency
            top_results_limit = AI_SUMMARY_CONFIG.get("top_results_limit", 10)
            limited_results = results[:top_results_limit]
            
            # Get field indices to include in summary
            summary_field_indices = AI_SUMMARY_CONFIG.get("summary_field_indices", [0, 1, 2, 3, 5, 7, 14, 15])
            
            # Build vendor summaries using field indices
            vendor_summaries = []
            for idx, vendor in enumerate(limited_results, 1):
                summary = {}
                
                # CRITICAL: Include match score and rank first
                score = vendor.get('similarity_score', 0)
                summary['Rank'] = f"#{idx}"
                summary['Match Score'] = f"{score:.1%}"
                
                for field_idx in summary_field_indices:
                    if field_idx not in FIELD_MAP:
                        continue
                    
                    field_config = FIELD_MAP[field_idx]
                    field_name = field_config["name"]
                    field_label = field_config["label"]
                    
                    # Get value from vendor
                    value = vendor.get(field_name) or vendor.get(f"field_{field_idx}")
                    
                    if value and str(value).strip() and str(value).lower() not in ['none', 'null', 'n/a']:
                        summary[field_label] = str(value).strip()
                
                if summary:  # Only add if has data
                    vendor_summaries.append(summary)
            
            # Format vendor summaries as text
            summaries_text = "\n\n".join([
                f"Result {i+1}:\n" + "\n".join([f"  - {k}: {v}" for k, v in vendor.items()])
                for i, vendor in enumerate(vendor_summaries)
            ])
            
            # Build prompt from template
            user_prompt_template = AI_SUMMARY_CONFIG.get("user_prompt_template", "")
            user_prompt = user_prompt_template.format(
                query=query,
                vendor_summaries=summaries_text,
                count=len(limited_results)
            )
            
            # Get system prompt
            system_prompt = AI_SUMMARY_CONFIG.get("system_prompt", "You are a helpful assistant.")
            
            # Generate summary
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=AI_SUMMARY_CONFIG.get("temperature", 0.7),
                max_tokens=AI_SUMMARY_CONFIG.get("max_tokens", 300)
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            # Fallback to legacy method if new config not available
            return self._generate_summary_legacy(results, query)
        except Exception as e:
            print(f"Error generating summary: {e}")
            error_message = AI_SUMMARY_CONFIG.get("error_message", "Unable to generate summary.")
            return error_message
    
    def _generate_summary_legacy(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Legacy summary generation - now uses field indices for database compatibility
        
        Maintains backward compatibility while using pure field index architecture.
        """
        if not results:
            return "No vendors were found matching your query."
        
        try:
            from config import FIELD_MAP, AI_SUMMARY_CONFIG
            
            # Get summary field indices from config
            summary_field_indices = AI_SUMMARY_CONFIG.get("summary_field_indices", [0, 1, 2, 3, 5, 6, 7, 11, 14, 15])
            
            # Prepare vendor summaries using field indices
            vendor_summaries = []
            for idx, vendor in enumerate(results[:10], 1):  # Limit to top 10 for token efficiency
                summary_dict = {}
                
                # CRITICAL: Include rank and match score first
                score = vendor.get('similarity_score', 0)
                summary_dict['Rank'] = f"#{idx}"
                summary_dict['Match Score'] = f"{score:.1%}"
                
                # Build summary from configured fields
                for field_idx in summary_field_indices:
                    if field_idx not in FIELD_MAP:
                        continue
                    
                    field_config = FIELD_MAP[field_idx]
                    field_name = field_config["name"]
                    label = field_config["label"]
                    
                    # Get value (try logical name first, then field_X format)
                    value = vendor.get(field_name) or vendor.get(f"field_{field_idx}")
                    
                    if value and str(value).lower() not in ['none', 'null', '']:
                        summary_dict[label] = value
                
                if summary_dict:  # Only add if has data
                    vendor_summaries.append(summary_dict)
            
            # Get GPT configuration
            temperature = AI_SUMMARY_CONFIG.get("temperature", 0.7)
            max_tokens = AI_SUMMARY_CONFIG.get("max_tokens", 300)
            system_prompt = AI_SUMMARY_CONFIG.get("system_prompt", 
                "You are a helpful assistant summarizing transport vendor search results.")
            user_prompt_template = AI_SUMMARY_CONFIG.get("user_prompt_template", 
                """Based on the user's query: "{query}"

Here are the top matching results:

{results}

Please provide a concise, helpful summary of these results. Include:
1. How many results were found
2. Key characteristics of the top matches
3. Any notable patterns or recommendations

Keep the summary conversational and under 150 words.""")
            
            # Format prompt using template
            prompt = user_prompt_template.format(query=query, results=vendor_summaries)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return self.format_results(results, format_type="brief")
    
    def generate_insights(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate insights about the search results using configurable field indices
        
        Args:
            results: Search results
            
        Returns:
            Dictionary with insights
        """
        if not results:
            return {'message': 'No results to analyze'}
        
        try:
            from config import AI_INSIGHTS_CONFIG, FIELD_MAP
            
            insights = {}
            
            # Location distribution (using configured field index)
            location_field_idx = AI_INSIGHTS_CONFIG.get("location_field_index", 3)
            if location_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[location_field_idx]["name"]
                locations = {}
                for vendor in results:
                    value = vendor.get(field_name) or vendor.get(f"field_{location_field_idx}")
                    if value:
                        locations[value] = locations.get(value, 0) + 1
                insights['top_states'] = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Category distribution (using configured field index)
            category_field_idx = AI_INSIGHTS_CONFIG.get("category_field_index", 5)
            if category_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[category_field_idx]["name"]
                categories = {}
                for vendor in results:
                    value = vendor.get(field_name) or vendor.get(f"field_{category_field_idx}")
                    if value:
                        for cat in str(value).split(','):
                            cat = cat.strip()
                            if cat:
                                categories[cat] = categories.get(cat, 0) + 1
                insights['common_vehicles'] = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Verification rate (using configured field index)
            verification_field_idx = AI_INSIGHTS_CONFIG.get("verification_field_index", 14)
            if verification_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[verification_field_idx]["name"]
                verified = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{verification_field_idx}") or "").lower() == 'verified')
                insights['verification_rate'] = f"{verified}/{len(results)} verified"
            
            # Binary features analysis
            binary_features = AI_INSIGHTS_CONFIG.get("binary_feature_indices", {})
            for field_idx, feature_name in binary_features.items():
                if field_idx in FIELD_MAP:
                    field_name = FIELD_MAP[field_idx]["name"]
                    count = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{field_idx}") or "").upper() == 'Y')
                    insights[f'{feature_name.lower().replace(" ", "_")}_rate'] = f"{count}/{len(results)} offer {feature_name.lower()}"
            
            # Owner vs Broker split
            owner_broker_idx = AI_INSIGHTS_CONFIG.get("owner_broker_field_index", 7)
            if owner_broker_idx in FIELD_MAP:
                field_name = FIELD_MAP[owner_broker_idx]["name"]
                owners = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{owner_broker_idx}") or "").lower() == 'owner')
                insights['owner_broker_split'] = f"{owners} owners, {len(results)-owners} brokers"
            
            return insights
            
        except ImportError:
            # Fallback to legacy method
            return self._generate_insights_legacy(results)
    
    def _generate_insights_legacy(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Legacy insights generation - now uses field indices for database compatibility
        
        Maintains backward compatibility while using pure field index architecture.
        """
        try:
            from config import FIELD_MAP, AI_INSIGHTS_CONFIG
            
            insights = {}
            
            # Location distribution using configured field index
            location_field_idx = AI_INSIGHTS_CONFIG.get("location_field_index", 3)  # Default to field_3 (vendor_state)
            if location_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[location_field_idx]["name"]
                locations = {}
                for vendor in results:
                    state = vendor.get(field_name) or vendor.get(f"field_{location_field_idx}")
                    if state:
                        locations[state] = locations.get(state, 0) + 1
                insights['top_states'] = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Vehicle types using configured field index
            category_field_idx = AI_INSIGHTS_CONFIG.get("category_field_index", 5)  # Default to field_5 (vehicle_type)
            if category_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[category_field_idx]["name"]
                vehicles = {}
                for vendor in results:
                    vehicle = vendor.get(field_name) or vendor.get(f"field_{category_field_idx}")
                    if vehicle:
                        for v in str(vehicle).split(','):
                            v = v.strip()
                            vehicles[v] = vehicles.get(v, 0) + 1
                insights['common_vehicles'] = sorted(vehicles.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Verification rate using configured field index
            verification_field_idx = AI_INSIGHTS_CONFIG.get("verification_field_index", 14)
            if verification_field_idx in FIELD_MAP:
                field_name = FIELD_MAP[verification_field_idx]["name"]
                verified = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{verification_field_idx}") or "").lower() == 'verified')
                insights['verification_rate'] = f"{verified}/{len(results)} verified"
            
            # Binary features (return service, etc.)
            binary_feature_indices = AI_INSIGHTS_CONFIG.get("binary_feature_indices", [11])  # Default to field_11 (return_service)
            for field_idx in binary_feature_indices:
                if field_idx in FIELD_MAP:
                    field_config = FIELD_MAP[field_idx]
                    field_name = field_config["name"]
                    feature_label = field_config["label"]
                    
                    count = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{field_idx}") or "").upper() == 'Y')
                    insights[f'{feature_label.lower().replace(" ", "_")}_rate'] = f"{count}/{len(results)} offer {feature_label.lower()}"
            
            # Owner vs Broker split using configured field index
            owner_broker_idx = AI_INSIGHTS_CONFIG.get("owner_broker_field_index", 7)
            if owner_broker_idx in FIELD_MAP:
                field_name = FIELD_MAP[owner_broker_idx]["name"]
                owners = sum(1 for v in results if (v.get(field_name) or v.get(f"field_{owner_broker_idx}") or "").lower() == 'owner')
                insights['owner_broker_split'] = f"{owners} owners, {len(results)-owners} brokers"
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights (legacy): {e}")
            return {"error": "Could not generate insights"}
    
    def answer_question(self, query: str, results: List[Dict[str, Any]], 
                       context: Optional[str] = None) -> str:
        """
        Answer a specific question about the results using GPT with configurable prompts
        
        Args:
            query: User's question
            results: Search results
            context: Additional context
            
        Returns:
            Natural language answer
        """
        try:
            from config import AI_QA_CONFIG, FIELD_MAP
            
            if not results:
                return AI_QA_CONFIG.get("no_results_message", "I couldn't find any relevant vendors to answer your question.")
            
            # Limit results for token efficiency
            top_results = AI_QA_CONFIG.get("top_results_for_qa", 5)
            limited_results = results[:top_results]
            
            # Get field indices to include in Q&A context
            qa_field_indices = AI_QA_CONFIG.get("qa_field_indices", [0, 1, 2, 3, 5, 6, 7, 11, 14, 15])
            
            # Build vendor data using field indices
            vendor_data = []
            for vendor in limited_results:
                vendor_info = {}
                
                for field_idx in qa_field_indices:
                    if field_idx not in FIELD_MAP:
                        continue
                    
                    field_config = FIELD_MAP[field_idx]
                    field_name = field_config["name"]
                    field_label = field_config["label"]
                    
                    # Get value
                    value = vendor.get(field_name) or vendor.get(f"field_{field_idx}")
                    
                    if value and str(value).strip() and str(value).lower() not in ['none', 'null', 'n/a']:
                        vendor_info[field_label] = str(value).strip()
                
                if vendor_info:
                    vendor_data.append(vendor_info)
            
            # Format vendor data as text
            vendor_data_text = "\n\n".join([
                f"Vendor {i+1}:\n" + "\n".join([f"  - {k}: {v}" for k, v in vendor.items()])
                for i, vendor in enumerate(vendor_data)
            ])
            
            # Build context string
            context_str = f"\nAdditional context: {context}" if context else ""
            
            # Build prompt from template
            user_prompt_template = AI_QA_CONFIG.get("user_prompt_template", "")
            user_prompt = user_prompt_template.format(
                query=query,
                context=context_str,
                vendor_data=vendor_data_text
            )
            
            # Get system prompt
            system_prompt = AI_QA_CONFIG.get("system_prompt", "You are a helpful assistant.")
            
            # Generate answer
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=AI_QA_CONFIG.get("temperature", 0.5),
                max_tokens=AI_QA_CONFIG.get("max_tokens", 250)
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            # Fallback to legacy method
            return self._answer_question_legacy(query, results, context)
        except Exception as e:
            print(f"Error generating answer: {e}")
            error_message = AI_QA_CONFIG.get("error_message", "Unable to answer the question.")
            return error_message
    
    def _answer_question_legacy(self, query: str, results: List[Dict[str, Any]], 
                                context: Optional[str] = None) -> str:
        """
        Legacy Q&A method - now uses field indices for database compatibility
        
        This method maintains backward compatibility while using the pure field index architecture.
        All field access is done through FIELD_MAP configuration.
        """
        if not results:
            return "I couldn't find any relevant vendors to answer your question."
        
        try:
            from config import FIELD_MAP, AI_QA_CONFIG
            
            # Get QA field indices from config (fallback to common fields)
            qa_field_indices = AI_QA_CONFIG.get("qa_field_indices", [0, 1, 2, 3, 5, 6, 7, 11, 14, 15])
            
            # Prepare vendor data using field indices
            vendor_data = []
            for v in results[:5]:
                vendor_dict = {}
                
                # Build vendor data from configured fields
                for field_idx in qa_field_indices:
                    if field_idx not in FIELD_MAP:
                        continue
                    
                    field_config = FIELD_MAP[field_idx]
                    field_name = field_config["name"]
                    label = field_config["label"]
                    
                    # Get value (try logical name first, then field_X format)
                    value = v.get(field_name) or v.get(f"field_{field_idx}")
                    
                    if value and str(value).lower() not in ['none', 'null', '']:
                        vendor_dict[label] = value
                
                if vendor_dict:  # Only add if has data
                    vendor_data.append(vendor_dict)
            
            # Create prompt
            context_str = f"\nAdditional context: {context}" if context else ""
            
            prompt = f"""Question: {query}{context_str}

Available vendor information:
{vendor_data}

Please answer the question based on the vendor data provided. Be specific and helpful."""
            
            # Get GPT settings from config
            temperature = AI_QA_CONFIG.get("temperature", 0.5)
            max_tokens = AI_QA_CONFIG.get("max_tokens", 250)
            system_prompt = AI_QA_CONFIG.get("system_prompt", 
                "You are a knowledgeable assistant helping with transport vendor queries.")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return self.format_results(results, format_type="brief")
