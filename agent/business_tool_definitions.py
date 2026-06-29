"""
Tool Definitions for Business Intelligence Tools
Complete CRUD operations for all 6 tables
For Groq function calling
"""

BUSINESS_TOOL_DEFINITIONS = [
    # ===== USERS TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_users",
            "description": "Query user database. Use to answer: 'How many users in Germany?', 'Show Pro plan users', 'Active users in Berlin', 'Users from TechNova'",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Filter by country (e.g., 'Germany')"},
                    "plan": {"type": "string", "description": "Filter by plan: Free/Pro/Enterprise"},
                    "city": {"type": "string", "description": "Filter by city (e.g., 'Berlin')"},
                    "active": {"type": "boolean", "description": "Filter by active status"},
                    "company": {"type": "string", "description": "Filter by company name"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_stats",
            "description": "Get user statistics: total, active %, by plan, by city. Use for: 'User statistics', 'How many active users?'",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    
    # ===== SALES TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_sales",
            "description": "Query sales data by country. Use for: 'Which country has the highest revenue?', 'Countries with high growth', 'Sales in France', 'Revenue data'",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Filter by country"},
                    "min_revenue": {"type": "integer", "description": "Minimum monthly revenue"},
                    "min_growth": {"type": "integer", "description": "Minimum yearly growth %"},
                    "max_churn": {"type": "number", "description": "Maximum churn rate %"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_countries",
            "description": "Get top countries by metric. Use for: 'Highest revenue country', 'Fastest growing country', 'Top 5 by users'",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": ["revenue", "growth", "users"], "description": "Metric to sort by"},
                    "limit": {"type": "integer", "description": "Number of countries (default: 5)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Get overall sales summary: total revenue, users, avg growth. Use for: 'Overall sales', 'Total revenue'",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    
    # ===== FEATURES TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_features",
            "description": "Query feature requests. Use for: 'High priority features', 'Planned features', 'Features with 100+ votes'",
            "parameters": {
                "type": "object",
                "properties": {
                    "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "description": "Filter by priority"},
                    "status": {"type": "string", "description": "Filter by status: Planned/In Progress/Completed/Backlog"},
                    "min_votes": {"type": "integer", "description": "Minimum votes"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_features",
            "description": "Get most voted features. Use for: 'Top requested features', 'Most popular features'",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of features (default: 5)"}
                }
            }
        }
    },
    
    # ===== TASKS TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_tasks",
            "description": "Query company tasks. Use for: 'In Progress tasks', 'Engineering tasks', 'Tasks assigned to Sarah'",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: Planned/In Progress/Completed/Blocked"},
                    "department": {"type": "string", "description": "Filter by department"},
                    "assignee": {"type": "string", "description": "Filter by assignee name"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_stats",
            "description": "Get task statistics: by status, by department. Use for: 'Task overview', 'How many completed tasks?'",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    
    # ===== DECISIONS TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_decisions",
            "description": "Query past decisions. Use for: 'How many decisions are approved?', 'High confidence decisions', 'Rejected decisions'",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: Approved/Rejected/In Review/Deferred"},
                    "min_confidence": {"type": "integer", "description": "Minimum confidence %"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar_decision",
            "description": "Search for similar past decisions. Use for: 'Did we decide about France?', 'Past expansion decisions'",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Question to search for"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_decision_stats",
            "description": "Get decision statistics. Use for: 'Decision overview', 'How many approved decisions?'",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    
    # ===== COMPETITORS TOOLS =====
    {
        "type": "function",
        "function": {
            "name": "query_competitors",
            "description": "Query competitors. Use for: 'Competitors in Germany', 'Top rated competitors', 'Competition analysis'",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Filter by country"},
                    "min_rating": {"type": "number", "description": "Minimum rating (e.g., 4.0)"},
                    "min_market_share": {"type": "integer", "description": "Minimum market share %"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_competitor_analysis",
            "description": "Get competitor analysis summary. Use for: 'Competitor overview', 'Market competition analysis'",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
