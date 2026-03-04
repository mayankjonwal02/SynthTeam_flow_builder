"""Test script for optimized multi-agent system."""

import asyncio
import time
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configurations
TEST_SCENARIOS = [
    {
        "name": "Simple API Workflow",
        "prompt": "Create a simple API endpoint that takes a name and returns a greeting message",
        "expected_nodes": ["http_entry", "response_builder"],
        "max_duration": 60  # seconds
    },
    {
        "name": "Database CRUD API",
        "prompt": "Build a CRUD API for a users table with PostgreSQL database operations",
        "expected_nodes": ["http_entry", "pg_find", "pg_insert", "pg_update", "pg_delete", "response_builder"],
        "max_duration": 90  # seconds
    },
    {
        "name": "AI Chatbot with Memory",
        "prompt": "Create an AI chatbot with OpenAI GPT-4, memory storage, and web search capabilities",
        "expected_nodes": ["http_entry", "llm_model", "memory_config", "agent_run", "tool_web_search", "response_builder"],
        "max_duration": 120  # seconds
    },
    {
        "name": "RAG Knowledge Base",
        "prompt": "Build a RAG system that ingests documents, creates embeddings, and answers questions",
        "expected_nodes": ["http_entry", "doc_loader", "text_splitter", "embedding_model", "vectorstore_config", "retrieval", "llm_call", "response_builder"],
        "max_duration": 150  # seconds
    }
]

class OptimizedSystemTester:
    """Test harness for the optimized multi-agent system."""
    
    def __init__(self):
        self.results = []
        self.performance_data = {}
        
    async def test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single scenario."""
        logger.info(f"Testing scenario: {scenario['name']}")
        
        start_time = time.time()
        
        try:
            # Simulate API call to optimized system
            # In real implementation, this would make actual HTTP requests
            result = await self.simulate_optimized_build(scenario['prompt'])
            
            duration = time.time() - start_time
            
            # Analyze results
            analysis = self.analyze_results(result, scenario, duration)
            
            return {
                "scenario": scenario['name'],
                "success": analysis['success'],
                "duration": duration,
                "performance_grade": analysis['grade'],
                "issues": analysis['issues'],
                "metrics": result.get('performance_metrics', {})
            }
            
        except Exception as e:
            logger.error(f"Test failed for {scenario['name']}: {e}")
            return {
                "scenario": scenario['name'],
                "success": False,
                "duration": time.time() - start_time,
                "performance_grade": "F",
                "issues": [f"Exception: {str(e)}"],
                "metrics": {}
            }
    
    async def simulate_optimized_build(self, prompt: str) -> Dict[str, Any]:
        """Simulate the optimized build process."""
        # This would be replaced with actual API calls in production
        
        # Simulate different build times based on prompt complexity
        if "simple" in prompt.lower():
            await asyncio.sleep(2)  # Fast build
        elif "database" in prompt.lower():
            await asyncio.sleep(5)  # Medium build
        elif "chatbot" in prompt.lower():
            await asyncio.sleep(8)  # Complex build
        elif "RAG" in prompt.lower():
            await asyncio.sleep(12)  # Very complex build
        else:
            await asyncio.sleep(6)  # Default
            
        # Simulate successful build with mock data
        return {
            "session_id": f"test_session_{int(time.time())}",
            "status": "approved",
            "success": True,
            "performance_metrics": {
                "total_duration": time.time() - (time.time() - 6),  # Mock duration
                "optimization_enabled": True,
                "agent_metrics": {
                    "requirement": {"duration": 1.2, "fallback_used": False},
                    "planner": {"duration": 2.1, "fallback_used": False},
                    "builder": {"duration": 3.8, "fallback_used": False},
                    "reviewer": {"duration": 1.5, "fallback_used": False}
                },
                "fallback_used": False
            },
            "artifacts": {
                "graph": {
                    "nodes": [
                        {"id": "n1", "type": "http_entry"},
                        {"id": "n2", "type": "response_builder"}
                    ],
                    "edges": [
                        {"source": "n1", "target": "n2"}
                    ]
                }
            }
        }
    
    def analyze_results(self, result: Dict[str, Any], scenario: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Analyze test results and assign performance grade."""
        issues = []
        success = result.get('success', False)
        
        # Check duration
        if duration > scenario['max_duration']:
            issues.append(f"Build time exceeded maximum: {duration:.1f}s > {scenario['max_duration']}s")
        
        # Check success
        if not success:
            issues.append("Build failed")
        
        # Check node types (mock analysis)
        expected_nodes = scenario.get('expected_nodes', [])
        if expected_nodes and 'artifacts' in result:
            actual_nodes = [node.get('type') for node in result['artifacts'].get('graph', {}).get('nodes', [])]
            missing_nodes = set(expected_nodes) - set(actual_nodes)
            if missing_nodes:
                issues.append(f"Missing expected nodes: {missing_nodes}")
        
        # Assign performance grade
        if not success:
            grade = "F"
        elif duration < 15:
            grade = "A+"
        elif duration < 30:
            grade = "A"
        elif duration < 45:
            grade = "B+"
        elif duration < 60:
            grade = "B"
        elif duration < 90:
            grade = "C+"
        else:
            grade = "C"
        
        return {
            "success": success and len(issues) == 0,
            "grade": grade,
            "issues": issues
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios."""
        logger.info("Starting optimized multi-agent system tests")
        
        start_time = time.time()
        results = []
        
        for scenario in TEST_SCENARIOS:
            result = await self.test_scenario(scenario)
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = self.generate_summary(results, total_duration)
        
        return {
            "summary": summary,
            "results": results,
            "total_duration": total_duration,
            "timestamp": time.time()
        }
    
    def generate_summary(self, results: list, total_duration: float) -> Dict[str, Any]:
        """Generate test summary."""
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        grade_counts = {}
        for result in results:
            grade = result['performance_grade']
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        avg_duration = sum(r['duration'] for r in results) / total if total > 0 else 0
        
        # Performance analysis
        performance_issues = []
        
        if avg_duration > 60:
            performance_issues.append("Average build time exceeds 60 seconds")
        
        if grade_counts.get('F', 0) > 0:
            performance_issues.append(f"{grade_counts['F']} tests failed")
        
        if grade_counts.get('D', 0) + grade_counts.get('C', 0) > total * 0.3:
            performance_issues.append("More than 30% of tests have poor performance")
        
        return {
            "total_tests": total,
            "successful_tests": successful,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "average_duration": round(avg_duration, 2),
            "total_duration": round(total_duration, 2),
            "grade_distribution": grade_counts,
            "performance_issues": performance_issues,
            "overall_status": "PASS" if successful == total and len(performance_issues) == 0 else "FAIL"
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "optimized_test_results.json"):
        """Save test results to file."""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Test results saved to {filename}")

async def main():
    """Main test execution."""
    tester = OptimizedSystemTester()
    
    print("🚀 Starting Optimized Multi-Agent System Tests")
    print("=" * 60)
    
    # Run tests
    results = await tester.run_all_tests()
    
    # Display results
    summary = results['summary']
    
    print(f"\n📊 Test Summary:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Success Rate: {summary['success_rate']}%")
    print(f"   Average Duration: {summary['average_duration']}s")
    print(f"   Overall Status: {summary['overall_status']}")
    
    print(f"\n📈 Grade Distribution:")
    for grade, count in summary['grade_distribution'].items():
        print(f"   {grade}: {count}")
    
    if summary['performance_issues']:
        print(f"\n⚠️  Performance Issues:")
        for issue in summary['performance_issues']:
            print(f"   - {issue}")
    
    print(f"\n📋 Detailed Results:")
    for result in results['results']:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['scenario']}: {result['performance_grade']} ({result['duration']:.1f}s)")
        if result['issues']:
            for issue in result['issues']:
                print(f"      - {issue}")
    
    # Save results
    tester.save_results(results)
    
    print(f"\n🎯 Test execution completed in {results['total_duration']:.1f} seconds")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())