import sys
sys.path.insert(0, 'c:\\Users\\kavya\\Desktop\\codes\\Let_Go_3.0\\backend')

import asyncio
from langchain_core.messages import HumanMessage

async def test_agent():
    try:
        from feature4.agent import agent_app
        print('Agent loaded successfully!')
        
        # Test the agent
        initial_state = {
            "messages": [HumanMessage(content="What subsidies are available for tractors?")],
            "user_profile": {"state": "Maharashtra"},
            "found_schemes": [],
            "selected_scheme": {},
            "application_status": "",
            "intent": ""
        }
        
        print("Running agent...")
        result = await agent_app.ainvoke(initial_state)
        
        print("\n=== RESULT ===")
        print(f"Messages: {len(result.get('messages', []))}")
        if result.get('messages'):
            print(f"Last message: {result['messages'][-1].content[:500]}...")
        print(f"Found schemes: {len(result.get('found_schemes', []))}")
        print(f"Intent: {result.get('intent')}")
        print("SUCCESS!")
        
    except Exception as e:
        import traceback
        print("ERROR:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
