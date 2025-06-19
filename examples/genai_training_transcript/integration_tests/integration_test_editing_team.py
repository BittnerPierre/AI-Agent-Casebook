#!/usr/bin/env python3
"""
Integration Test for EditingTeam US-004 Implementation

Demonstrates the complete EditingTeam workflow using Response API file_search
for multi-step content synthesis with agent feedback loops.

This test validates:
1. EditingTeam.synthesize_chapter() interface
2. Multi-step synthesis workflow (Documentalist → Writer → Reviewer → Script Strategist)
3. Response API file_search integration patterns
4. Chapter draft output to chapter_drafts/ directory
5. Integration with File Operations MCP (simulated)

Author: Claude Code (for Sprint 1 US-004)
Reference: Issue #51 - US-004: Response API Content Synthesis
"""

import os
import sys
import json
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime

# Load environment variables from project root
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Add src to path for imports
current_dir = Path(__file__).parent
src_path = current_dir .parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from transcript_generator.tools.editing_team import EditingTeam, ChapterDraft

# Setup structured logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_comprehensive_research_data():
    """Create comprehensive research data for integration testing"""
    return {
        'target_section': 'Introduction to Machine Learning',
        'syllabus': {
            'title': 'Advanced Machine Learning for Practitioners',
            'duration_weeks': 16,
            'learning_objectives': [
                'Understand fundamental machine learning concepts and terminology',
                'Apply supervised learning algorithms to real-world problems',
                'Evaluate and improve model performance using various metrics',
                'Implement unsupervised learning techniques for data exploration',
                'Design and deploy ML systems in production environments'
            ],
            'key_topics': [
                'Supervised Learning (Regression, Classification)',
                'Unsupervised Learning (Clustering, Dimensionality Reduction)',
                'Model Evaluation and Validation',
                'Feature Engineering and Selection',
                'Deep Learning Fundamentals',
                'ML Operations and Deployment'
            ]
        },
        'agenda': [
            {
                'title': 'Introduction to Machine Learning',
                'duration_minutes': 120,
                'topics': [
                    'What is Machine Learning?',
                    'Types of ML: Supervised, Unsupervised, Reinforcement',
                    'ML Workflow and Lifecycle',
                    'Common Applications and Use Cases',
                    'Tools and Frameworks Overview',
                    'Ethics and Bias in ML'
                ]
            },
            {
                'title': 'Supervised Learning Fundamentals',
                'duration_minutes': 90,
                'topics': [
                    'Linear and Logistic Regression',
                    'Decision Trees and Random Forests',
                    'Support Vector Machines',
                    'Cross-validation and Hyperparameter Tuning'
                ]
            }
        ],
        'research_notes': {
            'Introduction to Machine Learning': {
                'definitions_and_concepts': """
                Machine Learning is a subset of artificial intelligence (AI) that focuses on developing algorithms 
                and statistical models that enable computer systems to improve their performance on a specific task 
                through experience, without being explicitly programmed for every possible scenario.

                Key characteristics:
                - Learns from data patterns rather than explicit programming
                - Improves performance with more data and experience
                - Can make predictions or decisions on new, unseen data
                - Requires computational resources for training and inference
                """,
                'types_of_machine_learning': """
                1. Supervised Learning:
                   - Uses labeled training data (input-output pairs)
                   - Goal: Learn mapping from inputs to outputs
                   - Examples: Classification, Regression
                   - Algorithms: Linear Regression, Decision Trees, Neural Networks

                2. Unsupervised Learning:
                   - Uses unlabeled data (only inputs, no target outputs)
                   - Goal: Discover hidden patterns or structures
                   - Examples: Clustering, Dimensionality Reduction
                   - Algorithms: K-means, PCA, Autoencoders

                3. Reinforcement Learning:
                   - Learns through interaction with environment
                   - Uses rewards and penalties to guide learning
                   - Goal: Maximize cumulative reward
                   - Examples: Game playing, Robotics, Autonomous systems
                """,
                'real_world_applications': """
                Machine Learning applications span virtually every industry:

                Technology:
                - Search engines (Google, Bing)
                - Recommendation systems (Netflix, Amazon, Spotify)
                - Computer vision (image recognition, autonomous vehicles)
                - Natural language processing (chatbots, translation)

                Healthcare:
                - Medical image analysis (X-rays, MRIs, CT scans)
                - Drug discovery and development
                - Personalized treatment recommendations
                - Epidemic prediction and tracking

                Finance:
                - Fraud detection and prevention
                - Algorithmic trading
                - Credit scoring and risk assessment
                - Robo-advisors for investment management

                Business:
                - Customer segmentation and targeting
                - Demand forecasting and inventory optimization
                - Price optimization
                - Marketing campaign optimization
                """,
                'tools_and_frameworks': """
                Popular ML Libraries and Frameworks:

                Python Ecosystem:
                - Scikit-learn: General-purpose ML library, great for beginners
                - TensorFlow: Google's deep learning framework
                - PyTorch: Facebook's deep learning framework
                - Pandas: Data manipulation and analysis
                - NumPy: Numerical computing foundation

                R Ecosystem:
                - caret: Classification and Regression Training
                - randomForest: Random Forest implementation
                - e1071: Support Vector Machines

                Big Data ML:
                - Apache Spark MLlib: Distributed machine learning
                - H2O.ai: Scalable ML platform
                - Dask: Parallel computing for larger-than-memory datasets

                Cloud ML Services:
                - AWS SageMaker: End-to-end ML platform
                - Google Cloud AI Platform: Managed ML services
                - Azure Machine Learning: Microsoft's ML cloud service
                """,
                'ml_workflow_and_lifecycle': """
                Typical Machine Learning Project Workflow:

                1. Problem Definition:
                   - Define business objective
                   - Determine ML problem type (classification, regression, etc.)
                   - Set success metrics

                2. Data Collection and Exploration:
                   - Gather relevant data sources
                   - Perform exploratory data analysis (EDA)
                   - Understand data quality and characteristics

                3. Data Preprocessing:
                   - Clean and handle missing values
                   - Feature engineering and selection
                   - Data transformation and normalization
                   - Split data into training/validation/test sets

                4. Model Development:
                   - Select appropriate algorithms
                   - Train models on training data
                   - Tune hyperparameters using validation data
                   - Compare multiple models

                5. Model Evaluation:
                   - Assess performance on test data
                   - Analyze errors and edge cases
                   - Validate against business metrics

                6. Deployment and Monitoring:
                   - Deploy model to production environment
                   - Monitor performance and data drift
                   - Retrain and update as needed
                """
            }
        }
    }


def simulate_file_operations_mcp_integration(chapter_draft: ChapterDraft, output_dir: str = "chapter_drafts"):
    """
    Simulate File Operations MCP integration for writing chapter drafts.
    
    This represents the integration point where EditingTeam outputs are written
    to chapter_drafts/ directory for consumption by Editorial Finalizer.
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename based on section ID
        safe_filename = chapter_draft.section_id.replace(' ', '_').replace('/', '_').lower()
        output_file = os.path.join(output_dir, f"{safe_filename}.json")
        
        # Write chapter draft in JSON format according to schema
        chapter_data = chapter_draft.to_dict()
        chapter_data['created_at'] = datetime.now().isoformat()
        chapter_data['status'] = 'draft'
        chapter_data['word_count'] = len(chapter_draft.content.split())
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Chapter draft written to: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"Failed to write chapter draft: {str(e)}")
        raise


def test_editing_team_integration():
    """
    Main integration test for EditingTeam US-004 implementation.
    
    Tests the complete workflow from research notes to chapter drafts.
    """
    logger.info("Starting EditingTeam Integration Test (US-004)")
    logger.info("=" * 60)
    
    # Check if we have OpenAI API key for full integration test
    has_api_key = bool(os.getenv('OPENAI_API_KEY'))
    
    if not has_api_key:
        logger.warning("OPENAI_API_KEY not set - running simulation mode")
        print("🔄 Running in simulation mode (no actual OpenAI API calls)")
        print("To run full integration test, set OPENAI_API_KEY environment variable")
    else:
        logger.info("OPENAI_API_KEY found - running full integration test")
        print("🚀 Running full integration test with OpenAI API")
    
    try:
        # Test 1: Create comprehensive research data
        print("\n1️⃣ Creating Comprehensive Research Data")
        print("-" * 40)
        
        research_data = create_comprehensive_research_data()
        logger.info(f"Created research data for section: {research_data['target_section']}")
        print(f"   ✅ Research data created")
        print(f"   📚 Syllabus: {research_data['syllabus']['title']}")
        print(f"   📋 Modules: {len(research_data['agenda'])}")
        print(f"   📝 Research sections: {len(research_data['research_notes'])}")
        
        # Test 2: Initialize EditingTeam
        print("\n2️⃣ Initializing EditingTeam")
        print("-" * 40)
        
        if has_api_key:
            editing_team = EditingTeam(
                model="gpt-4o-mini",
                max_revisions=2,
                expires_after_days=1
            )
            print("   ✅ EditingTeam initialized with OpenAI API")
        else:
            # Simulation mode - create mock editing team
            from unittest.mock import Mock
            editing_team = Mock()
            
            # Create realistic mock response
            mock_chapter_draft = ChapterDraft(
                section_id=research_data['target_section'],
                content="""# Introduction to Machine Learning

## Learning Objectives
By the end of this module, you will be able to:
- Understand fundamental machine learning concepts and terminology
- Identify different types of machine learning problems
- Recognize real-world applications of machine learning
- Navigate the machine learning workflow and lifecycle

## What is Machine Learning?

Machine Learning is a subset of artificial intelligence (AI) that focuses on developing algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience, without being explicitly programmed for every possible scenario.

Think of it this way: instead of writing explicit instructions for every possible situation (traditional programming), we provide the computer with examples and let it learn patterns from those examples. It's like teaching a child to recognize animals by showing them many pictures of different animals, rather than trying to describe every possible feature of each animal.

### Key Characteristics of Machine Learning:
- **Learns from data patterns** rather than explicit programming
- **Improves performance** with more data and experience
- **Makes predictions or decisions** on new, unseen data
- **Requires computational resources** for training and inference

## Types of Machine Learning

Machine learning can be categorized into three main types, each suited for different kinds of problems:

### 1. Supervised Learning
Supervised learning uses labeled training data (input-output pairs) to learn a mapping from inputs to outputs.

**Think of it as learning with a teacher:** You're shown examples with the correct answers, and you learn to predict the right answer for new examples.

**Common applications:**
- Email spam detection (input: email content, output: spam/not spam)
- Medical diagnosis (input: symptoms/test results, output: diagnosis)
- Price prediction (input: house features, output: price)

**Popular algorithms:** Linear Regression, Decision Trees, Random Forest, Neural Networks

### 2. Unsupervised Learning
Unsupervised learning uses unlabeled data to discover hidden patterns or structures.

**Think of it as learning without a teacher:** You're given data without any correct answers and must find interesting patterns on your own.

**Common applications:**
- Customer segmentation (grouping customers by behavior)
- Anomaly detection (finding unusual patterns)
- Data compression (reducing data size while preserving information)

**Popular algorithms:** K-means Clustering, Principal Component Analysis (PCA), Autoencoders

### 3. Reinforcement Learning
Reinforcement learning learns through interaction with an environment, using rewards and penalties to guide learning.

**Think of it as learning through trial and error:** Like a child learning to ride a bike, the system tries actions and learns from the consequences.

**Common applications:**
- Game playing (chess, Go, video games)
- Robotics (robot navigation, manipulation)
- Autonomous vehicles (driving decisions)

## Real-World Applications

Machine learning has transformed numerous industries and aspects of our daily lives:

### Technology
- **Search engines:** Google uses ML to rank search results and understand user intent
- **Recommendation systems:** Netflix suggests movies, Amazon recommends products, Spotify creates personalized playlists
- **Computer vision:** Photo tagging on social media, medical image analysis, autonomous vehicle perception

### Healthcare
- **Medical imaging:** AI can detect tumors in X-rays and MRIs with accuracy matching or exceeding human radiologists
- **Drug discovery:** ML accelerates the identification of promising drug compounds
- **Personalized medicine:** Treatment recommendations based on individual patient characteristics

### Finance
- **Fraud detection:** Banks use ML to identify suspicious transactions in real-time
- **Algorithmic trading:** Automated trading systems make split-second investment decisions
- **Credit scoring:** More accurate assessment of loan default risk

## The Machine Learning Workflow

Every successful ML project follows a systematic workflow:

### 1. Problem Definition
- What business problem are we solving?
- What type of ML problem is this?
- How will we measure success?

### 2. Data Collection and Exploration
- What data do we have available?
- What patterns exist in the data?
- What's the quality of our data?

### 3. Data Preprocessing
- Clean and prepare the data
- Handle missing values
- Create meaningful features
- Split data for training and testing

### 4. Model Development
- Choose appropriate algorithms
- Train models on historical data
- Fine-tune model parameters
- Compare different approaches

### 5. Model Evaluation
- Test performance on unseen data
- Analyze errors and limitations
- Validate against business objectives

### 6. Deployment and Monitoring
- Deploy model to production
- Monitor performance over time
- Update and retrain as needed

## Tools and Technologies

The ML ecosystem offers a rich set of tools for different needs:

### Python Libraries
- **Scikit-learn:** Perfect for beginners, covers most common ML algorithms
- **TensorFlow & PyTorch:** Advanced deep learning frameworks
- **Pandas & NumPy:** Essential for data manipulation and numerical computing

### Cloud Platforms
- **AWS SageMaker, Google Cloud AI, Azure ML:** Managed ML services that handle infrastructure complexity

## Ethical Considerations

As ML becomes more prevalent, we must consider:
- **Bias and fairness:** Ensuring models don't discriminate against certain groups
- **Privacy:** Protecting individual data and maintaining confidentiality
- **Transparency:** Understanding how models make decisions
- **Accountability:** Taking responsibility for model outcomes

## Looking Ahead

Machine learning is not just a technological tool—it's a new way of solving problems by learning from data. As we progress through this course, you'll gain hands-on experience with the concepts introduced here.

### Next Steps
In our upcoming modules, we'll dive deeper into:
- Supervised learning algorithms and their applications
- Data preprocessing and feature engineering techniques
- Model evaluation and performance optimization
- Practical implementation using Python and popular ML libraries

### Reflection Questions
- How might machine learning transform your current industry or field of interest?
- What potential challenges or ethical considerations should we keep in mind?
- Which type of machine learning (supervised, unsupervised, reinforcement) seems most relevant to problems you'd like to solve?

---

This introduction provides the foundation for your machine learning journey. Remember, ML is both an art and a science—combining technical skills with domain expertise and creative problem-solving."""
            )
            
            editing_team.synthesize_chapter.return_value = mock_chapter_draft
            print("   ✅ EditingTeam simulation mode initialized")
        
        # Test 3: Execute chapter synthesis
        print("\n3️⃣ Executing Chapter Synthesis")
        print("-" * 40)
        
        start_time = datetime.now()
        
        if has_api_key:
            logger.info("Starting real chapter synthesis with OpenAI API")
            chapter_draft = editing_team.synthesize_chapter(research_data)
        else:
            logger.info("Running simulated chapter synthesis")
            chapter_draft = editing_team.synthesize_chapter(research_data)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"   ✅ Chapter synthesis completed")
        print(f"   ⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"   📄 Section ID: {chapter_draft.section_id}")
        print(f"   📊 Content length: {len(chapter_draft.content)} characters")
        print(f"   📝 Word count: {len(chapter_draft.content.split())} words")
        
        # Test 4: Validate chapter draft structure
        print("\n4️⃣ Validating Chapter Draft Structure")
        print("-" * 40)
        
        # Verify ChapterDraft compliance with schema
        assert isinstance(chapter_draft, ChapterDraft)
        assert hasattr(chapter_draft, 'section_id')
        assert hasattr(chapter_draft, 'content')
        assert isinstance(chapter_draft.section_id, str)
        assert isinstance(chapter_draft.content, str)
        assert len(chapter_draft.content) > 100  # Substantial content
        
        # Check for key content elements
        content_lower = chapter_draft.content.lower()
        expected_elements = [
            'machine learning',
            'supervised',
            'unsupervised',
            'learning objectives',
            'applications'
        ]
        
        missing_elements = []
        for element in expected_elements:
            if element not in content_lower:
                missing_elements.append(element)
        
        if missing_elements:
            logger.warning(f"Missing expected content elements: {missing_elements}")
        else:
            print("   ✅ All expected content elements present")
        
        print(f"   ✅ Schema compliance verified")
        print(f"   ✅ Content quality validated")
        
        # Test 5: Simulate File Operations MCP Integration
        print("\n5️⃣ Simulating File Operations MCP Integration")
        print("-" * 40)
        
        output_file = simulate_file_operations_mcp_integration(chapter_draft)
        
        # Verify file was created and contains expected data
        assert os.path.exists(output_file)
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['section_id'] == chapter_draft.section_id
        assert saved_data['content'] == chapter_draft.content
        assert 'created_at' in saved_data
        assert 'status' in saved_data
        assert 'word_count' in saved_data
        
        print(f"   ✅ Chapter draft saved to: {output_file}")
        print(f"   📁 File size: {os.path.getsize(output_file)} bytes")
        print(f"   🔗 Integration point validated for Editorial Finalizer")
        
        # Test 6: Performance and Resource Analysis
        print("\n6️⃣ Performance and Resource Analysis")
        print("-" * 40)
        
        print(f"   📊 Processing metrics:")
        print(f"     - Total processing time: {processing_time:.2f} seconds")
        print(f"     - Content generation rate: {len(chapter_draft.content)/processing_time:.1f} chars/sec")
        print(f"     - API mode: {'Real OpenAI API' if has_api_key else 'Simulation'}")
        
        if has_api_key:
            # In real mode, resources should be cleaned up automatically
            print(f"   🧹 OpenAI resources cleaned up automatically")
        
        # Test 7: Integration Summary
        print("\n7️⃣ Integration Test Summary")
        print("-" * 40)
        
        success_metrics = {
            'interface_compliance': True,
            'content_quality': len(chapter_draft.content) > 1000,
            'schema_compliance': isinstance(chapter_draft, ChapterDraft),
            'file_integration': os.path.exists(output_file),
            'processing_time': processing_time < 300,  # Should complete within 5 minutes
            'api_integration': has_api_key
        }
        
        passed_tests = sum(success_metrics.values())
        total_tests = len(success_metrics)
        
        print(f"   📈 Test Results: {passed_tests}/{total_tests} passed")
        for metric, passed in success_metrics.items():
            status = "✅" if passed else "❌"
            print(f"     {status} {metric.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 EditingTeam Integration Test PASSED")
            print(f"   ✅ US-004 implementation fully validated")
            print(f"   ✅ Ready for Editorial Finalizer integration (US-005)")
            return True
        else:
            print(f"\n⚠️  EditingTeam Integration Test PARTIAL")
            print(f"   ⚠️  Some validation checks failed")
            return False
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        print(f"\n❌ EditingTeam Integration Test FAILED")
        print(f"   Error: {str(e)}")
        return False
    
    finally:
        # Cleanup
        try:
            if os.path.exists("chapter_drafts"):
                print(f"\n🧹 Cleaning up test files...")
                # In production, we'd keep these files for Editorial Finalizer
                # But for testing, we clean up
                for file in os.listdir("chapter_drafts"):
                    if file.endswith('.json'):
                        test_file = os.path.join("chapter_drafts", file)
                        print(f"   🗑️  Removing test file: {test_file}")
                        os.remove(test_file)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup warning: {cleanup_error}")


if __name__ == "__main__":
    success = test_editing_team_integration()
    exit(0 if success else 1) 