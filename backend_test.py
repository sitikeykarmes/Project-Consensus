#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime

class ChatPlatformTester:
    def __init__(self, base_url="https://5d10c056-feba-400a-8bdd-24c73b33dae3.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {message}")
        
        self.test_results.append({
            "test": name,
            "passed": success,
            "message": message
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        default_headers = {'Content-Type': 'application/json'}
        if self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            default_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=default_headers, timeout=10)
            elif method == 'POST':
                if isinstance(data, dict) and 'Content-Type' in default_headers and 'application/json' in default_headers['Content-Type']:
                    response = requests.post(url, json=data, headers=default_headers, timeout=10)
                else:
                    response = requests.post(url, data=data, headers=default_headers, timeout=10)

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"raw_response": response.text}

            message = f"Status: {response.status_code}"
            if not success:
                message += f", Expected: {expected_status}, Response: {response_data}"

            self.log_test(name, success, message)
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_signup(self, email, password):
        """Test user signup"""
        success, response = self.run_test(
            "Signup User",
            "POST",
            f"api/auth/signup?email={email}&password={password}",
            200
        )
        return success

    def test_login(self, email, password):
        """Test user login"""
        # Prepare form data as specified in the requirements
        form_data = {
            'username': email,  # Note: username field is email
            'password': password
        }
        
        # Remove Content-Type header for form data
        headers_without_json = {}
        if self.token:
            headers_without_json['Authorization'] = f'Bearer {self.token}'
            
        success, response = self.run_test(
            "Login User",
            "POST",
            "api/auth/login",
            200,
            data=form_data,
            headers=headers_without_json
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response.get('user', {})
            print(f"📋 Token acquired: {self.token[:20]}...")
            return True
        return False

    def test_get_agents(self):
        """Test get available agents"""
        success, response = self.run_test(
            "Get Available Agents",
            "GET",
            "api/agents",
            200
        )
        
        if success:
            agents = response.get('agents', [])
            expected_count = 3
            if len(agents) == expected_count:
                print(f"📋 Found {len(agents)} agents as expected")
                return True
            else:
                print(f"⚠️  Expected {expected_count} agents, found {len(agents)}")
                return False
        return False

    def test_get_my_groups(self):
        """Test get user's groups"""
        if not self.token:
            self.log_test("Get My Groups", False, "No token available")
            return False
            
        success, response = self.run_test(
            "Get My Groups",
            "GET",
            "api/groups/my",
            200
        )
        return success

    def test_create_group(self):
        """Test group creation with agents"""
        if not self.token:
            self.log_test("Create Group", False, "No token available")
            return None
            
        group_data = {
            "name": f"Test Group {datetime.now().strftime('%H%M%S')}",
            "agents": ["agent_research", "agent_analysis", "agent_synthesis"],
            "member_emails": []
        }
        
        success, response = self.run_test(
            "Create Group with Agents",
            "POST",
            "api/groups/create",
            200,
            data=group_data
        )
        
        if success and 'group' in response and 'id' in response['group']:
            group_id = response['group']['id']
            print(f"📋 Created group with ID: {group_id}")
            return group_id
        return None

    def test_root_endpoint(self):
        """Test root endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success

def main():
    print("🚀 Starting Multi-Agent Chat Platform Backend Tests")
    print("=" * 60)
    
    tester = ChatPlatformTester()
    
    # Generate unique test credentials
    timestamp = datetime.now().strftime('%H%M%S')
    test_email = f"test_{timestamp}@test.com"
    test_password = "test123"
    
    print(f"📋 Test credentials: {test_email} / {test_password}")
    
    # Test sequence
    tests_results = []
    
    # 1. Test root endpoint
    tests_results.append(tester.test_root_endpoint())
    
    # 2. Test signup
    tests_results.append(tester.test_signup(test_email, test_password))
    
    # 3. Test login
    tests_results.append(tester.test_login(test_email, test_password))
    
    # 4. Test get agents
    tests_results.append(tester.test_get_agents())
    
    # 5. Test get groups (should work even if empty)
    tests_results.append(tester.test_get_my_groups())
    
    # 6. Test group creation
    group_id = tester.test_create_group()
    tests_results.append(group_id is not None)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print("💥 Some backend tests failed!")
        print("\nFailed Tests:")
        for result in tester.test_results:
            if not result['passed']:
                print(f"  ❌ {result['test']}: {result['message']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())