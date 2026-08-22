import sys
import json
import os
sys.path.append("/root/sarkari-result-portal")
from universal_design_agent import UniversalDesignAgent
from rebuild_all_universal_posts import posts_data

agent = UniversalDesignAgent()
for data in posts_data:
    print(f"Publishing {data['title']}...")
    agent.publish(data)

print("Done generating with UniversalDesignAgent!")
