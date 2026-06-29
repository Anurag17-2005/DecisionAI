"""
Business Intelligence Tools for DynamoDB
Complete CRUD operations for: users, sales, feature_requests, tasks, decisions, competitors
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any
from datetime import datetime

load_dotenv()

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def convert_to_decimals(obj):
    """Convert float objects to Decimal for DynamoDB storage"""
    if isinstance(obj, list):
        return [convert_to_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

# ==================== USERS TABLE ====================

def query_users(country: Optional[str] = None, plan: Optional[str] = None, 
                city: Optional[str] = None, active: Optional[bool] = None,
                company: Optional[str] = None) -> Dict:
    """
    Query users with filters. Use this to answer questions like:
    - "How many users are from Germany?"
    - "Show me active users"
    - "List Pro plan users"
    
    Args:
        country: Filter by country (e.g., "Germany")
        plan: Filter by plan (Free/Pro/Enterprise)
        city: Filter by city
        active: Filter by active status
        company: Filter by company name
    """
    try:
        table = dynamodb.Table('users')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if country:
            items = [u for u in items if u.get('country', '').lower() == country.lower()]
        if plan:
            items = [u for u in items if u.get('plan', '').lower() == plan.lower()]
        if city:
            items = [u for u in items if u.get('city', '').lower() == city.lower()]
        if active is not None:
            items = [u for u in items if u.get('active') == active]
        if company:
            items = [u for u in items if company.lower() in u.get('company', '').lower()]
        
        items = convert_decimals(items)
        
        # If large result, return summary instead of all data
        if len(items) > 10:
            active_count = len([u for u in items if u.get("active")])
            
            # Group by plan
            plan_breakdown = {}
            for u in items:
                plan_name = u.get("plan", "Unknown")
                plan_breakdown[plan_name] = plan_breakdown.get(plan_name, 0) + 1
            
            # Group by city (top 5)
            city_breakdown = {}
            for u in items:
                city_name = u.get("city", "Unknown")
                city_breakdown[city_name] = city_breakdown.get(city_name, 0) + 1
            
            top_cities = dict(sorted(city_breakdown.items(), key=lambda x: x[1], reverse=True)[:5])
            
            return {
                "success": True,
                "total_count": len(items),
                "active_count": active_count,
                "active_percentage": round((active_count/len(items))*100, 1),
                "by_plan": plan_breakdown,
                "top_cities": top_cities
            }
        
        return {
            "success": True,
            "count": len(items),
            "users": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_stats() -> Dict:
    """Get user statistics (total, by plan, by country, active %)"""
    try:
        table = dynamodb.Table('users')
        response = table.scan()
        items = response['Items']
        
        total = len(items)
        active = len([u for u in items if u.get('active')])
        
        # Count by plan
        plans = {}
        for user in items:
            plan = user.get('plan', 'Unknown')
            plans[plan] = plans.get(plan, 0) + 1
        
        # Count by city
        cities = {}
        for user in items:
            city = user.get('city', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
        
        return {
            "success": True,
            "statistics": {
                "total_users": total,
                "active_users": active,
                "active_percentage": round((active/total)*100, 1) if total > 0 else 0,
                "by_plan": plans,
                "by_city": cities
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_user(user_id: str, name: str, country: str, city: str,
                company: str, plan: str, active: bool = True) -> Dict:
    """Create a new user"""
    try:
        table = dynamodb.Table('users')
        item = {
            'user_id': user_id,
            'name': name,
            'country': country,
            'city': city,
            'company': company,
            'plan': plan,
            'active': active,
            'signup_date': datetime.now().strftime('%Y-%m-%d')
        }
        table.put_item(Item=item)
        return {"success": True, "message": f"User {user_id} created", "user": convert_decimals(item)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user(user_id: str, updates: Dict[str, Any]) -> Dict:
    """Update user fields"""
    try:
        table = dynamodb.Table('users')
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"User {user_id} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_user(user_id: str) -> Dict:
    """Delete a user"""
    try:
        table = dynamodb.Table('users')
        table.delete_item(Key={'user_id': user_id})
        return {"success": True, "message": f"User {user_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== SALES TABLE ====================

def query_sales(country: Optional[str] = None, min_revenue: Optional[int] = None,
                min_growth: Optional[int] = None, max_churn: Optional[float] = None) -> Dict:
    """
    Query sales data with filters. Use this to answer:
    - "Which country has the highest revenue?"
    - "Show countries with growth > 25%"
    - "Sales data for Germany"
    
    Args:
        country: Filter by specific country
        min_revenue: Minimum monthly revenue
        min_growth: Minimum yearly growth percentage
        max_churn: Maximum churn rate
    """
    try:
        table = dynamodb.Table('sales')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if country:
            items = [s for s in items if s.get('country', '').lower() == country.lower()]
        if min_revenue:
            items = [s for s in items if float(s.get('monthly_revenue', 0)) >= min_revenue]
        if min_growth:
            items = [s for s in items if float(s.get('yearly_growth', 0)) >= min_growth]
        if max_churn:
            items = [s for s in items if float(s.get('churn_rate', 100)) <= max_churn]
        
        items = convert_decimals(items)
        
        # If returning all sales data, provide summary
        if not country and len(items) > 5:
            total_revenue = sum(s.get("monthly_revenue", 0) for s in items)
            total_users = sum(s.get("active_users", 0) for s in items)
            avg_growth = sum(s.get("yearly_growth", 0) for s in items) / len(items)
            
            # Sort by revenue and keep top 5
            top_5 = sorted(items, key=lambda x: x.get("monthly_revenue", 0), reverse=True)[:5]
            
            return {
                "success": True,
                "summary": {
                    "total_countries": len(items),
                    "total_monthly_revenue": round(total_revenue, 2),
                    "total_users": total_users,
                    "average_growth": round(avg_growth, 1)
                },
                "top_5_countries": top_5
            }
        
        return {
            "success": True,
            "count": len(items),
            "sales": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_top_countries(metric: str = "revenue", limit: int = 5) -> Dict:
    """
    Get top countries by metric. Use for:
    - "Top 5 countries by revenue"
    - "Fastest growing countries"
    
    Args:
        metric: revenue/growth/users (default: revenue)
        limit: Number of top countries to return
    """
    try:
        table = dynamodb.Table('sales')
        response = table.scan()
        items = convert_decimals(response['Items'])
        
        # Sort by metric
        if metric == "revenue":
            items.sort(key=lambda x: x.get('monthly_revenue', 0), reverse=True)
        elif metric == "growth":
            items.sort(key=lambda x: x.get('yearly_growth', 0), reverse=True)
        elif metric == "users":
            items.sort(key=lambda x: x.get('active_users', 0), reverse=True)
        
        top = items[:limit]
        
        return {
            "success": True,
            "metric": metric,
            "top_countries": top
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_sales_summary() -> Dict:
    """Get overall sales summary (total revenue, avg growth, etc.)"""
    try:
        table = dynamodb.Table('sales')
        response = table.scan()
        items = response['Items']
        
        total_revenue = sum(float(s.get('monthly_revenue', 0)) for s in items)
        total_users = sum(int(s.get('active_users', 0)) for s in items)
        avg_growth = sum(float(s.get('yearly_growth', 0)) for s in items) / len(items) if items else 0
        avg_churn = sum(float(s.get('churn_rate', 0)) for s in items) / len(items) if items else 0
        
        return {
            "success": True,
            "summary": {
                "total_monthly_revenue": round(total_revenue, 2),
                "total_active_users": total_users,
                "average_growth": round(avg_growth, 1),
                "average_churn": round(avg_churn, 1),
                "countries": len(items)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_sales_record(country: str, active_users: int, monthly_revenue: float,
                       yearly_growth: float, churn_rate: float) -> Dict:
    """Create a new sales record for a country"""
    try:
        table = dynamodb.Table('sales')
        item = convert_to_decimals({
            'country': country,
            'active_users': active_users,
            'monthly_revenue': monthly_revenue,
            'yearly_growth': yearly_growth,
            'churn_rate': churn_rate,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        })
        table.put_item(Item=item)
        return {"success": True, "message": f"Sales record for {country} created", "record": convert_decimals(item)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_sales_record(country: str, updates: Dict[str, Any]) -> Dict:
    """Update sales record for a country"""
    try:
        table = dynamodb.Table('sales')
        updates = convert_to_decimals(updates)
        updates['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'country': country},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"Sales record for {country} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_sales_record(country: str) -> Dict:
    """Delete sales record for a country"""
    try:
        table = dynamodb.Table('sales')
        table.delete_item(Key={'country': country})
        return {"success": True, "message": f"Sales record for {country} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== FEATURE REQUESTS TABLE ====================

def query_features(priority: Optional[str] = None, status: Optional[str] = None,
                   min_votes: Optional[int] = None) -> Dict:
    """
    Query feature requests with filters
    
    Args:
        priority: High/Medium/Low
        status: Planned/In Progress/Completed/Backlog
        min_votes: Minimum number of votes
    """
    try:
        table = dynamodb.Table('feature_requests')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if priority:
            items = [f for f in items if f.get('priority', '').lower() == priority.lower()]
        if status:
            items = [f for f in items if f.get('status', '').lower() == status.lower()]
        if min_votes:
            items = [f for f in items if int(f.get('votes', 0)) >= min_votes]
        
        # Sort by votes descending
        items.sort(key=lambda x: x.get('votes', 0), reverse=True)
        items = convert_decimals(items)
        
        return {
            "success": True,
            "count": len(items),
            "features": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_top_features(limit: int = 5) -> Dict:
    """Get most voted feature requests"""
    try:
        table = dynamodb.Table('feature_requests')
        response = table.scan()
        items = convert_decimals(response['Items'])
        
        items.sort(key=lambda x: x.get('votes', 0), reverse=True)
        top = items[:limit]
        
        return {
            "success": True,
            "top_features": top
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_feature_request(feature_id: str, feature_name: str, priority: str,
                           estimated_weeks: int, status: str = "Backlog", votes: int = 0) -> Dict:
    """Create a new feature request"""
    try:
        table = dynamodb.Table('feature_requests')
        item = {
            'feature_id': feature_id,
            'feature_name': feature_name,
            'votes': votes,
            'priority': priority,
            'estimated_weeks': estimated_weeks,
            'status': status
        }
        table.put_item(Item=item)
        return {"success": True, "message": f"Feature {feature_id} created", "feature": item}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_feature_request(feature_id: str, updates: Dict[str, Any]) -> Dict:
    """Update feature request"""
    try:
        table = dynamodb.Table('feature_requests')
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'feature_id': feature_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"Feature {feature_id} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_feature_request(feature_id: str) -> Dict:
    """Delete a feature request"""
    try:
        table = dynamodb.Table('feature_requests')
        table.delete_item(Key={'feature_id': feature_id})
        return {"success": True, "message": f"Feature {feature_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== TASKS TABLE ====================

def query_tasks(status: Optional[str] = None, department: Optional[str] = None,
                assignee: Optional[str] = None) -> Dict:
    """
    Query company tasks with filters
    
    Args:
        status: Planned/In Progress/Completed/Blocked
        department: Strategy/Engineering/Marketing/etc
        assignee: Person's name
    """
    try:
        table = dynamodb.Table('tasks')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if status:
            items = [t for t in items if t.get('status', '').lower() == status.lower()]
        if department:
            items = [t for t in items if t.get('department', '').lower() == department.lower()]
        if assignee:
            items = [t for t in items if assignee.lower() in t.get('assignee', '').lower()]
        
        items = convert_decimals(items)
        
        return {
            "success": True,
            "count": len(items),
            "tasks": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_task_stats() -> Dict:
    """Get task statistics (by status, by department)"""
    try:
        table = dynamodb.Table('tasks')
        response = table.scan()
        items = response['Items']
        
        # Count by status
        by_status = {}
        for task in items:
            status = task.get('status', 'Unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # Count by department
        by_dept = {}
        for task in items:
            dept = task.get('department', 'Unknown')
            by_dept[dept] = by_dept.get(dept, 0) + 1
        
        return {
            "success": True,
            "statistics": {
                "total_tasks": len(items),
                "by_status": by_status,
                "by_department": by_dept
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_task(task_id: str, title: str, department: str,
                assignee: str, status: str = "Planned", due_date: Optional[str] = None) -> Dict:
    """Create a new task"""
    try:
        table = dynamodb.Table('tasks')
        item = {
            'task_id': task_id,
            'title': title,
            'department': department,
            'assignee': assignee,
            'status': status,
            'due_date': due_date or datetime.now().strftime('%Y-%m-%d')
        }
        table.put_item(Item=item)
        return {"success": True, "message": f"Task {task_id} created", "task": item}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_task(task_id: str, updates: Dict[str, Any]) -> Dict:
    """Update task fields"""
    try:
        table = dynamodb.Table('tasks')
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'task_id': task_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"Task {task_id} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_task(task_id: str) -> Dict:
    """Delete a task"""
    try:
        table = dynamodb.Table('tasks')
        table.delete_item(Key={'task_id': task_id})
        return {"success": True, "message": f"Task {task_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== DECISIONS TABLE ====================

def query_decisions(status: Optional[str] = None, min_confidence: Optional[int] = None) -> Dict:
    """
    Query past decisions with filters. Use for:
    - "How many decisions are approved?"
    - "Show high confidence decisions"
    
    Args:
        status: Approved/Rejected/In Review/Deferred/In Progress/Completed
        min_confidence: Minimum confidence percentage
    """
    try:
        table = dynamodb.Table('decisions')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if status:
            items = [d for d in items if d.get('status', '').lower() == status.lower()]
        if min_confidence:
            items = [d for d in items if float(d.get('confidence', 0)) >= min_confidence]
        
        # Sort by confidence descending
        items.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        items = convert_decimals(items)
        
        return {
            "success": True,
            "count": len(items),
            "decisions": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_similar_decision(question: str) -> Dict:
    """Search for similar past decisions by question text"""
    try:
        table = dynamodb.Table('decisions')
        response = table.scan()
        items = response['Items']
        
        # Simple text matching
        matches = []
        question_lower = question.lower()
        for decision in items:
            q = decision.get('question', '').lower()
            if any(word in q for word in question_lower.split() if len(word) > 3):
                matches.append(decision)
        
        matches = convert_decimals(matches)
        
        return {
            "success": True,
            "count": len(matches),
            "similar_decisions": matches
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_decision_stats() -> Dict:
    """Get decision statistics (by status, avg confidence)"""
    try:
        table = dynamodb.Table('decisions')
        response = table.scan()
        items = response['Items']
        
        # Count by status
        by_status = {}
        for decision in items:
            status = decision.get('status', 'Unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        # Average confidence
        avg_confidence = sum(float(d.get('confidence', 0)) for d in items) / len(items) if items else 0
        
        return {
            "success": True,
            "statistics": {
                "total_decisions": len(items),
                "by_status": by_status,
                "average_confidence": round(avg_confidence, 1)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_decision(decision_id: str, question: str, recommendation: str,
                   confidence: float, status: str = "In Review") -> Dict:
    """Create a new decision record"""
    try:
        table = dynamodb.Table('decisions')
        item = convert_to_decimals({
            'decision_id': decision_id,
            'question': question,
            'recommendation': recommendation,
            'confidence': confidence,
            'status': status,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        })
        table.put_item(Item=item)
        return {"success": True, "message": f"Decision {decision_id} created", "decision": convert_decimals(item)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_decision(decision_id: str, updates: Dict[str, Any]) -> Dict:
    """Update decision fields"""
    try:
        table = dynamodb.Table('decisions')
        updates = convert_to_decimals(updates)
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'decision_id': decision_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"Decision {decision_id} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_decision(decision_id: str) -> Dict:
    """Delete a decision"""
    try:
        table = dynamodb.Table('decisions')
        table.delete_item(Key={'decision_id': decision_id})
        return {"success": True, "message": f"Decision {decision_id} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==================== COMPETITORS TABLE ====================

def query_competitors(country: Optional[str] = None, min_rating: Optional[float] = None,
                     min_market_share: Optional[int] = None) -> Dict:
    """
    Query competitors with filters
    
    Args:
        country: Filter by country
        min_rating: Minimum rating (e.g., 4.0)
        min_market_share: Minimum market share percentage
    """
    try:
        table = dynamodb.Table('competitors')
        response = table.scan()
        items = response['Items']
        
        # Apply filters
        if country:
            items = [c for c in items if c.get('country', '').lower() == country.lower()]
        if min_rating:
            items = [c for c in items if float(c.get('rating', 0)) >= min_rating]
        if min_market_share:
            items = [c for c in items if float(c.get('market_share', 0)) >= min_market_share]
        
        # Sort by market share descending
        items.sort(key=lambda x: x.get('market_share', 0), reverse=True)
        items = convert_decimals(items)
        
        return {
            "success": True,
            "count": len(items),
            "competitors": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_competitor_analysis() -> Dict:
    """Get competitor analysis summary"""
    try:
        table = dynamodb.Table('competitors')
        response = table.scan()
        items = response['Items']
        
        total_competitors = len(items)
        avg_rating = sum(float(c.get('rating', 0)) for c in items) / total_competitors if total_competitors > 0 else 0
        total_market_share = sum(float(c.get('market_share', 0)) for c in items)
        
        # Top by market share
        items.sort(key=lambda x: x.get('market_share', 0), reverse=True)
        top_3 = items[:3]
        
        items = convert_decimals(items)
        top_3 = convert_decimals(top_3)
        
        return {
            "success": True,
            "analysis": {
                "total_competitors": total_competitors,
                "average_rating": round(avg_rating, 2),
                "total_market_share": round(total_market_share, 1),
                "top_3_by_market_share": top_3
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_competitor(company: str, country: str, pricing: str,
                     market_share: float, rating: float) -> Dict:
    """Create a new competitor record"""
    try:
        table = dynamodb.Table('competitors')
        item = convert_to_decimals({
            'company': company,
            'country': country,
            'pricing': pricing,
            'market_share': market_share,
            'rating': rating
        })
        table.put_item(Item=item)
        return {"success": True, "message": f"Competitor {company} created", "competitor": convert_decimals(item)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_competitor(company: str, updates: Dict[str, Any]) -> Dict:
    """Update competitor fields"""
    try:
        table = dynamodb.Table('competitors')
        updates = convert_to_decimals(updates)
        update_expr = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expr_values = {f":{k}": v for k, v in updates.items()}
        
        table.update_item(
            Key={'company': company},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        return {"success": True, "message": f"Competitor {company} updated"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_competitor(company: str) -> Dict:
    """Delete a competitor"""
    try:
        table = dynamodb.Table('competitors')
        table.delete_item(Key={'company': company})
        return {"success": True, "message": f"Competitor {company} deleted"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== TOOL FUNCTIONS MAP ====================

BUSINESS_TOOL_FUNCTIONS = {
    # Users - Read
    "query_users": query_users,
    "get_user_stats": get_user_stats,
    # Users - Create/Update/Delete
    "create_user": create_user,
    "update_user": update_user,
    "delete_user": delete_user,
    
    # Sales - Read
    "query_sales": query_sales,
    "get_top_countries": get_top_countries,
    "get_sales_summary": get_sales_summary,
    # Sales - Create/Update/Delete
    "create_sales_record": create_sales_record,
    "update_sales_record": update_sales_record,
    "delete_sales_record": delete_sales_record,
    
    # Features - Read
    "query_features": query_features,
    "get_top_features": get_top_features,
    # Features - Create/Update/Delete
    "create_feature_request": create_feature_request,
    "update_feature_request": update_feature_request,
    "delete_feature_request": delete_feature_request,
    
    # Tasks - Read
    "query_tasks": query_tasks,
    "get_task_stats": get_task_stats,
    # Tasks - Create/Update/Delete
    "create_task": create_task,
    "update_task": update_task,
    "delete_task": delete_task,
    
    # Decisions - Read
    "query_decisions": query_decisions,
    "search_similar_decision": search_similar_decision,
    "get_decision_stats": get_decision_stats,
    # Decisions - Create/Update/Delete
    "create_decision": create_decision,
    "update_decision": update_decision,
    "delete_decision": delete_decision,
    
    # Competitors - Read
    "query_competitors": query_competitors,
    "get_competitor_analysis": get_competitor_analysis,
    # Competitors - Create/Update/Delete
    "create_competitor": create_competitor,
    "update_competitor": update_competitor,
    "delete_competitor": delete_competitor
}
