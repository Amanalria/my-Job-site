import sys
import os
sys.path.append("/root/sarkari-result-portal")
from universal_design_agent import UniversalDesignAgent
from rebuild_all_universal_posts import posts_data
import vacancy_lifecycle_engine
# Mock out the slow audit so it doesn't commit automatically
vacancy_lifecycle_engine.audit_and_execute_lifecycle = lambda: None

agent = UniversalDesignAgent()
for data in posts_data:
    agent.publish(data)
