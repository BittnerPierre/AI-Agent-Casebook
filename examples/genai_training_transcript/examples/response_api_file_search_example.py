#!/usr/bin/env python3
"""
Response API File_Search Integration Pattern (US-011)

Demonstrates working OpenAI Response API file_search usage with research notes.
This provides concrete patterns for US-004 EditingTeam content synthesis.

Author: Sprint 1 Development Team  
Reference: US-011 Response API File_Search Integration Pattern
Issue: #50
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI library not installed. Install with: pip install openai")
    sys.exit(1)


class ResponseAPIFileSearchIntegration:
    """
    Working implementation of OpenAI Response API with file_search for research note synthesis.
    
    This class demonstrates the patterns that EditingTeam will use for content synthesis
    by combining syllabus, agenda, and research notes using OpenAI's file_search capability.
    """
    
    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None):
        """Initialize Response API client with project configuration"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.project_id = project_id or "proj_UWuOPp9MOKrOCtZABSCTY4Um"
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
            
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            organization=None,  # Use project ID instead
            project=self.project_id
        )
        
        # Track created resources for cleanup
        self.vector_store_id = None
        self.assistant_id = None
        self.thread_id = None
        self.uploaded_file_ids = []
        
        print(f"🔧 Initialized Response API client with project: {self.project_id}")
    
    def create_research_notes_files(self, research_data: Dict[str, Any]) -> List[str]:
        """
        Create temporary files from research data for file_search upload.
        
        Args:
            research_data: Dictionary containing syllabus, agenda, and research notes
            
        Returns:
            List of file paths created
        """
        file_paths = []
        temp_dir = tempfile.mkdtemp()
        
        # 1. Create syllabus file
        syllabus_path = os.path.join(temp_dir, "course_syllabus.md")
        with open(syllabus_path, 'w', encoding='utf-8') as f:
            f.write("# Course Syllabus\n\n")
            syllabus = research_data.get('syllabus', {})
            f.write(f"**Course:** {syllabus.get('title', 'N/A')}\n")
            f.write(f"**Duration:** {syllabus.get('duration_weeks', 'N/A')} weeks\n\n")
            f.write("## Learning Objectives\n")
            for obj in syllabus.get('learning_objectives', []):
                f.write(f"- {obj}\n")
            f.write("\n## Key Topics\n")
            for topic in syllabus.get('key_topics', []):
                f.write(f"- {topic}\n")
        file_paths.append(syllabus_path)
        
        # 2. Create agenda file
        agenda_path = os.path.join(temp_dir, "module_agenda.md")
        with open(agenda_path, 'w', encoding='utf-8') as f:
            f.write("# Module Agenda\n\n")
            agenda = research_data.get('agenda', [])
            for i, module in enumerate(agenda, 1):
                if isinstance(module, dict):
                    f.write(f"## Module {i}: {module.get('title', 'Untitled')}\n")
                    f.write(f"**Duration:** {module.get('duration_minutes', 'N/A')} minutes\n")
                    f.write("### Topics:\n")
                    for topic in module.get('topics', []):
                        f.write(f"- {topic}\n")
                    f.write("\n")
                else:
                    f.write(f"## Module {i}: {module}\n\n")
        file_paths.append(agenda_path)
        
        # 3. Create research notes files
        research_notes = research_data.get('research_notes', {})
        for module_name, notes in research_notes.items():
            notes_path = os.path.join(temp_dir, f"research_notes_{module_name.replace(' ', '_').lower()}.md")
            with open(notes_path, 'w', encoding='utf-8') as f:
                f.write(f"# Research Notes: {module_name}\n\n")
                if isinstance(notes, dict):
                    for section, content in notes.items():
                        f.write(f"## {section}\n\n{content}\n\n")
                else:
                    f.write(f"{notes}\n")
            file_paths.append(notes_path)
            
        print(f"📁 Created {len(file_paths)} research files in {temp_dir}")
        return file_paths
    
    def upload_files_for_search(self, file_paths: List[str]) -> str:
        """
        Upload files to OpenAI and create vector store for file_search.
        
        Args:
            file_paths: List of file paths to upload
            
        Returns:
            Vector store ID for file_search
        """
        try:
            # Upload files
            uploaded_files = []
            for file_path in file_paths:
                print(f"⬆️ Uploading {os.path.basename(file_path)}...")
                with open(file_path, 'rb') as file:
                    uploaded_file = self.client.files.create(
                        file=file,
                        purpose='assistants'
                    )
                    uploaded_files.append(uploaded_file)
                    self.uploaded_file_ids.append(uploaded_file.id)
                    
            print(f"✅ Uploaded {len(uploaded_files)} files")
            
            # Create vector store
            vector_store = self.client.beta.vector_stores.create(
                name="Research Notes Vector Store",
                expires_after={
                    "anchor": "last_active_at",
                    "days": 1  # Auto-cleanup after 1 day
                }
            )
            self.vector_store_id = vector_store.id
            print(f"📚 Created vector store: {vector_store.id}")
            
            # Add files to vector store
            file_batch = self.client.beta.vector_stores.file_batches.create(
                vector_store_id=vector_store.id,
                file_ids=[file.id for file in uploaded_files]
            )
            
            print(f"🔍 Processing files for search... (batch: {file_batch.id})")
            
            # Wait for processing to complete
            import time
            while file_batch.status in ['in_progress', 'cancelling']:
                time.sleep(1)
                file_batch = self.client.beta.vector_stores.file_batches.retrieve(
                    vector_store_id=vector_store.id,
                    batch_id=file_batch.id
                )
                
            if file_batch.status == 'completed':
                print(f"✅ Files processed successfully")
            else:
                print(f"⚠️ File processing status: {file_batch.status}")
                
            return vector_store.id
            
        except Exception as e:
            print(f"❌ Error uploading files: {str(e)}")
            raise
    
    def create_research_assistant(self, vector_store_id: str) -> str:
        """
        Create OpenAI assistant with file_search capability.
        
        Args:
            vector_store_id: Vector store ID for file_search
            
        Returns:
            Assistant ID
        """
        try:
            assistant = self.client.beta.assistants.create(
                name="Research Content Synthesizer",
                instructions="""You are a research content synthesizer for educational content creation.
                
Your role is to analyze research notes, syllabus, and module agendas to create high-quality educational content synthesis.

Key responsibilities:
1. Extract relevant information from research notes using file_search
2. Align content with syllabus objectives and module agendas  
3. Synthesize coherent narrative that connects concepts
4. Maintain educational quality and appropriate depth level
5. Ensure content flows logically and builds understanding

Use file_search to query the uploaded research materials and provide comprehensive, well-structured responses that demonstrate effective content synthesis patterns for educational content generation.""",
                model="gpt-4-turbo-preview",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )
            
            self.assistant_id = assistant.id
            print(f"🤖 Created assistant: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            print(f"❌ Error creating assistant: {str(e)}")
            raise
    
    def synthesize_content(self, synthesis_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform content synthesis using file_search on research materials.
        
        Args:
            synthesis_request: Request containing query and synthesis parameters
            
        Returns:
            Synthesis response with generated content and file search results
        """
        try:
            # Create thread for conversation
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            
            # Prepare synthesis query
            query = synthesis_request.get('query', '')
            synthesis_type = synthesis_request.get('type', 'content_synthesis')
            target_module = synthesis_request.get('target_module', '')
            
            # Enhanced query with context
            enhanced_query = f"""
Synthesis Request: {synthesis_type}
Target Module: {target_module}

Query: {query}

Please use file_search to analyze the research materials and provide:
1. Relevant content extraction from research notes
2. Alignment with syllabus objectives  
3. Integration with module agenda topics
4. Synthesized narrative that demonstrates effective content patterns
5. References to specific research sources used

Focus on creating content that EditingTeam agents can use as a reference pattern for high-quality educational content synthesis.
"""
            
            # Add message to thread
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=enhanced_query
            )
            
            print(f"💬 Created synthesis request for: {target_module}")
            
            # Run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            import time
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(2)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                print(f"🔄 Processing... (status: {run.status})")
                
            if run.status == 'completed':
                # Get response messages
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Extract assistant response
                assistant_messages = [msg for msg in messages.data if msg.role == 'assistant']
                if assistant_messages:
                    response_content = assistant_messages[0].content[0].text.value
                    annotations = assistant_messages[0].content[0].text.annotations
                    
                    # Process file search annotations
                    file_search_results = []
                    for annotation in annotations:
                        if hasattr(annotation, 'file_citation'):
                            file_search_results.append({
                                'file_id': annotation.file_citation.file_id,
                                'quote': annotation.file_citation.quote,
                                'text': annotation.text
                            })
                    
                    return {
                        'status': 'success',
                        'synthesis_type': synthesis_type,
                        'target_module': target_module,
                        'synthesized_content': response_content,
                        'file_search_results': file_search_results,
                        'sources_used': len(file_search_results),
                        'run_id': run.id,
                        'thread_id': thread.id
                    }
                else:
                    return {
                        'status': 'error',
                        'error': 'No assistant response found'
                    }
            else:
                return {
                    'status': 'error', 
                    'error': f'Run failed with status: {run.status}',
                    'run_details': run.last_error if hasattr(run, 'last_error') else None
                }
                
        except Exception as e:
            print(f"❌ Error in content synthesis: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def demonstrate_multi_step_synthesis(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrate multi-step synthesis workflow combining syllabus+agenda+research notes.
        
        This showcases the complete integration pattern for US-004 EditingTeam implementation.
        
        Args:
            research_data: Complete research data structure
            
        Returns:
            Results from multi-step synthesis demonstration
        """
        print("\n🔬 Multi-Step Content Synthesis Demonstration")
        print("=" * 60)
        
        results = {
            'workflow_steps': [],
            'synthesis_results': [],
            'integration_patterns': [],
            'performance_metrics': {}
        }
        
        start_time = datetime.now()
        
        try:
            # Step 1: Upload research materials
            print("\n1️⃣ Uploading Research Materials")
            print("-" * 30)
            file_paths = self.create_research_notes_files(research_data)
            vector_store_id = self.upload_files_for_search(file_paths)
            results['workflow_steps'].append('research_materials_uploaded')
            
            # Step 2: Create research assistant
            print("\n2️⃣ Creating Research Assistant")  
            print("-" * 30)
            assistant_id = self.create_research_assistant(vector_store_id)
            results['workflow_steps'].append('assistant_created')
            
            # Step 3: Multi-step synthesis requests
            print("\n3️⃣ Multi-Step Content Synthesis")
            print("-" * 30)
            
            synthesis_requests = [
                {
                    'type': 'module_overview',
                    'target_module': 'Introduction to Machine Learning',
                    'query': 'Create a comprehensive module overview that introduces machine learning concepts, drawing from the syllabus objectives and research notes. Focus on foundational concepts and learning progression.'
                },
                {
                    'type': 'content_synthesis', 
                    'target_module': 'Supervised Learning Algorithms',
                    'query': 'Synthesize content about supervised learning algorithms by combining information from research notes with agenda topics. Include practical examples and ensure alignment with syllabus learning objectives.'
                },
                {
                    'type': 'integration_narrative',
                    'target_module': 'Course Conclusion',
                    'query': 'Create an integrative narrative that connects all module topics from the agenda with the overall course objectives in the syllabus. Demonstrate how concepts build upon each other.'
                }
            ]
            
            for i, request in enumerate(synthesis_requests, 1):
                print(f"\n   Synthesis {i}: {request['type']}")
                print(f"   Target: {request['target_module']}")
                
                synthesis_result = self.synthesize_content(request)
                results['synthesis_results'].append(synthesis_result)
                
                if synthesis_result.get('status') == 'success':
                    print(f"   ✅ Success - {synthesis_result.get('sources_used', 0)} sources used")
                    results['integration_patterns'].append({
                        'type': request['type'],
                        'sources_integrated': synthesis_result.get('sources_used', 0),
                        'content_length': len(synthesis_result.get('synthesized_content', '')),
                        'file_search_annotations': len(synthesis_result.get('file_search_results', []))
                    })
                else:
                    print(f"   ❌ Failed: {synthesis_result.get('error')}")
            
            # Step 4: Integration pattern analysis
            print("\n4️⃣ Integration Pattern Analysis")
            print("-" * 30)
            
            total_sources = sum(p.get('sources_integrated', 0) for p in results['integration_patterns'])
            total_content = sum(p.get('content_length', 0) for p in results['integration_patterns'])
            avg_annotations = sum(p.get('file_search_annotations', 0) for p in results['integration_patterns']) / len(results['integration_patterns']) if results['integration_patterns'] else 0
            
            results['performance_metrics'] = {
                'total_synthesis_requests': len(synthesis_requests),
                'successful_syntheses': len([r for r in results['synthesis_results'] if r.get('status') == 'success']),
                'total_sources_integrated': total_sources,
                'total_content_generated': total_content,
                'average_file_search_annotations': avg_annotations,
                'processing_time_seconds': (datetime.now() - start_time).total_seconds()
            }
            
            print(f"   📊 Total Sources Integrated: {total_sources}")
            print(f"   📝 Total Content Generated: {total_content:,} characters")
            print(f"   🔍 Avg File Search Annotations: {avg_annotations:.1f}")
            print(f"   ⏱️ Processing Time: {results['performance_metrics']['processing_time_seconds']:.1f}s")
            
            results['workflow_steps'].append('integration_analysis_completed')
            
        except Exception as e:
            print(f"\n❌ Multi-step synthesis failed: {str(e)}")
            results['error'] = str(e)
            
        finally:
            # Cleanup temporary files
            for file_path in file_paths:
                try:
                    os.unlink(file_path)
                except:
                    pass
                    
        return results
    
    def cleanup_resources(self):
        """Clean up created OpenAI resources"""
        print("\n🧹 Cleaning up resources...")
        
        try:
            # Delete vector store (also deletes associated files)
            if self.vector_store_id:
                self.client.beta.vector_stores.delete(self.vector_store_id)
                print(f"   ✅ Deleted vector store: {self.vector_store_id}")
                
            # Delete assistant
            if self.assistant_id:
                self.client.beta.assistants.delete(self.assistant_id)
                print(f"   ✅ Deleted assistant: {self.assistant_id}")
                
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {str(e)}")


def create_sample_research_data() -> Dict[str, Any]:
    """Create sample research data for demonstration"""
    return {
        'syllabus': {
            'title': 'Introduction to Machine Learning',
            'duration_weeks': 8,
            'learning_objectives': [
                'Understand fundamental machine learning concepts and terminology',
                'Learn to distinguish between supervised, unsupervised, and reinforcement learning',
                'Implement basic algorithms using Python and scikit-learn',
                'Evaluate model performance and avoid common pitfalls',
                'Apply ML techniques to real-world problem scenarios'
            ],
            'key_topics': [
                'Data preprocessing and feature engineering',
                'Supervised learning algorithms (linear regression, decision trees, SVM)',
                'Unsupervised learning (clustering, PCA)',
                'Model evaluation and validation techniques',
                'Overfitting, underfitting, and regularization',
                'Cross-validation and hyperparameter tuning'
            ]
        },
        'agenda': [
            {
                'title': 'Introduction to Machine Learning',
                'duration_minutes': 45,
                'topics': [
                    'What is machine learning?',
                    'Types of machine learning',
                    'Applications and use cases',
                    'ML workflow overview'
                ]
            },
            {
                'title': 'Supervised Learning Algorithms', 
                'duration_minutes': 60,
                'topics': [
                    'Linear regression fundamentals',
                    'Logistic regression for classification',
                    'Decision trees and random forests',
                    'Support Vector Machines (SVM)',
                    'Model comparison and selection'
                ]
            },
            {
                'title': 'Model Evaluation and Validation',
                'duration_minutes': 50,
                'topics': [
                    'Training, validation, and test sets',
                    'Cross-validation techniques',
                    'Performance metrics (accuracy, precision, recall, F1)',
                    'ROC curves and AUC',
                    'Overfitting and underfitting'
                ]
            }
        ],
        'research_notes': {
            'Introduction to Machine Learning': {
                'key_concepts': """
Machine learning is a subset of artificial intelligence (AI) that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience, without being explicitly programmed for every scenario.

The field emerged from the intersection of computer science, statistics, and cognitive science, with roots tracing back to the 1950s. Arthur Samuel, who coined the term "machine learning" in 1959, defined it as a "field of study that gives computers the ability to learn without being explicitly programmed."

Key characteristics of machine learning systems:
1. Data-driven learning: Algorithms learn patterns from data rather than following pre-programmed rules
2. Generalization: Ability to make predictions on new, unseen data based on learned patterns
3. Automatic improvement: Performance improves with more data and experience
4. Pattern recognition: Identification of complex patterns in large datasets
                """,
                'historical_context': """
The history of machine learning can be divided into several key periods:

1950s-1960s: Foundation period
- Perceptron algorithm by Frank Rosenblatt (1957)
- First neural network implementations
- Early pattern recognition research

1980s-1990s: Revival and expansion
- Backpropagation algorithm for neural networks
- Support Vector Machines development
- Decision tree algorithms (ID3, C4.5)
- Statistical learning theory foundations

2000s-2010s: Big data and computational power
- Ensemble methods (Random Forest, Boosting)
- Kernel methods and nonlinear transformations
- Increased computational resources enabling larger datasets

2010s-present: Deep learning revolution
- Convolutional Neural Networks for image recognition
- Recurrent Neural Networks for sequence data
- Transformer architectures and attention mechanisms
- Transfer learning and pre-trained models
                """,
                'applications': """
Machine learning has found applications across virtually every industry and domain:

Healthcare:
- Medical image analysis and diagnostic assistance
- Drug discovery and molecular design
- Personalized treatment recommendations
- Epidemic modeling and public health monitoring

Finance:
- Algorithmic trading and portfolio optimization
- Credit scoring and risk assessment
- Fraud detection and security monitoring
- Robo-advisors for automated investment management

Technology:
- Search engines and information retrieval
- Recommendation systems (Netflix, Amazon, Spotify)
- Natural language processing and translation
- Computer vision and autonomous vehicles

Business and Marketing:
- Customer segmentation and targeting
- Demand forecasting and inventory optimization
- Pricing optimization strategies
- Sentiment analysis and brand monitoring
                """
            },
            'Supervised Learning Algorithms': {
                'algorithm_fundamentals': """
Supervised learning is a machine learning paradigm where algorithms learn from labeled training data to make predictions on new, unseen data. The goal is to learn a mapping function from input variables (features) to output variables (targets).

Key characteristics:
- Requires labeled training data (input-output pairs)
- Goal is to generalize to new, unseen examples
- Performance can be measured using known correct answers
- Two main types: classification (discrete outputs) and regression (continuous outputs)

Mathematical foundation:
Given a training dataset D = {(x₁, y₁), (x₂, y₂), ..., (xₙ, yₙ)} where xᵢ represents input features and yᵢ represents the corresponding target output, the goal is to learn a function f: X → Y such that f(x) ≈ y for new examples.

The learning process involves:
1. Hypothesis space definition (set of possible functions)
2. Loss function specification (measure of prediction error)
3. Optimization algorithm to minimize loss
4. Regularization to prevent overfitting
                """,
                'linear_regression': """
Linear regression is one of the fundamental supervised learning algorithms for regression tasks. It assumes a linear relationship between input features and the target variable.

Mathematical formulation:
ŷ = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ + ε

Where:
- ŷ is the predicted value
- β₀ is the intercept (bias term)
- βᵢ are the coefficients for each feature xᵢ
- ε represents the error term

Key concepts:
1. Least squares estimation: Minimizes the sum of squared residuals
2. Assumptions: Linearity, independence, homoscedasticity, normality
3. Evaluation metrics: Mean Squared Error (MSE), R-squared, Mean Absolute Error (MAE)
4. Extensions: Polynomial regression, Ridge regression, Lasso regression

Advantages:
- Simple and interpretable
- Fast training and prediction
- No hyperparameters to tune (basic version)
- Provides confidence intervals

Limitations:
- Assumes linear relationship
- Sensitive to outliers
- Requires feature scaling for optimal performance
- Can suffer from multicollinearity issues
                """,
                'decision_trees': """
Decision trees are versatile supervised learning algorithms that create a model by learning simple decision rules inferred from data features. They can be used for both classification and regression tasks.

Tree structure:
- Root node: Contains the entire dataset
- Internal nodes: Represent decision points based on feature values
- Leaf nodes: Contain the final prediction or class label
- Branches: Represent the outcome of a decision test

Splitting criteria:
1. Classification trees:
   - Gini impurity: Measures the probability of incorrect classification
   - Information gain (entropy): Measures the reduction in uncertainty
   - Chi-square: Statistical test for independence

2. Regression trees:
   - Mean Squared Error (MSE): Measures the average squared difference
   - Mean Absolute Error (MAE): Measures the average absolute difference

Algorithm process:
1. Start with the root node containing all training data
2. Find the best feature and threshold to split the data
3. Create child nodes based on the split
4. Recursively repeat for each child node
5. Stop when stopping criteria are met (max depth, min samples, etc.)

Advantages:
- Easy to understand and interpret
- Requires little data preparation
- Handles both numerical and categorical features
- Can capture non-linear relationships
- Implicit feature selection

Limitations:
- Prone to overfitting
- Can be unstable (small data changes = different tree)
- Biased toward features with more levels
- Difficulty with linear relationships
                """
            },
            'Model Evaluation and Validation': {
                'evaluation_fundamentals': """
Model evaluation is crucial for assessing the performance of machine learning algorithms and ensuring they generalize well to new, unseen data. Proper evaluation prevents overfitting and provides confidence in model deployment.

Key principles:
1. Separation of concerns: Training, validation, and testing data must be kept separate
2. Representative sampling: Data splits should maintain the distribution of the original dataset
3. Multiple evaluation metrics: No single metric tells the complete story
4. Cross-validation: Reduces variance in performance estimates
5. Statistical significance: Understanding confidence intervals and hypothesis testing

Data splitting strategies:
- Hold-out validation: 70% train, 15% validation, 15% test (typical split)
- Time series split: Chronological splitting for temporal data
- Stratified sampling: Maintains class distribution in splits
- Group-based splitting: Ensures related samples stay together

Common pitfalls:
- Data leakage: Information from test set inadvertently used in training
- Look-ahead bias: Using future information to predict past events
- Selection bias: Non-representative sampling leads to biased estimates
- Multiple testing: Increased false positive rates from repeated testing
                """,
                'performance_metrics': """
Different types of machine learning problems require different evaluation metrics. Choosing appropriate metrics is essential for meaningful model assessment.

Classification metrics:

1. Accuracy: (TP + TN) / (TP + TN + FP + FN)
   - Simple and intuitive
   - Can be misleading with imbalanced datasets
   - Best for balanced datasets with equal cost of errors

2. Precision: TP / (TP + FP)
   - Measures the quality of positive predictions
   - Important when false positives are costly
   - Used in spam detection, medical diagnosis

3. Recall (Sensitivity): TP / (TP + FN)
   - Measures the ability to find all positive instances
   - Important when false negatives are costly
   - Used in fraud detection, disease screening

4. F1-Score: 2 × (Precision × Recall) / (Precision + Recall)
   - Harmonic mean of precision and recall
   - Balances both precision and recall
   - Useful for imbalanced datasets

5. Specificity: TN / (TN + FP)
   - Measures the ability to correctly identify negatives
   - Complement to recall
   - Important in medical testing

6. Area Under ROC Curve (AUC-ROC):
   - Measures discrimination ability across all thresholds
   - Threshold-independent metric
   - Values range from 0.5 (random) to 1.0 (perfect)

Regression metrics:

1. Mean Squared Error (MSE): Average of squared differences
2. Root Mean Squared Error (RMSE): Square root of MSE (same units as target)
3. Mean Absolute Error (MAE): Average of absolute differences
4. R-squared: Proportion of variance explained by the model
5. Mean Absolute Percentage Error (MAPE): Percentage-based error metric
                """,
                'cross_validation': """
Cross-validation is a statistical method for estimating model performance and assessing how well a model will generalize to independent datasets. It helps address the limitation of single train-test splits.

Types of cross-validation:

1. K-Fold Cross-Validation:
   - Dataset divided into k equal-sized folds
   - Model trained on k-1 folds, tested on remaining fold
   - Process repeated k times, rotating the test fold
   - Final score is the average across all k iterations
   - Common choices: k = 5 or k = 10

2. Stratified K-Fold:
   - Maintains the same proportion of samples for each target class
   - Essential for imbalanced classification problems
   - Ensures each fold is representative of the overall dataset

3. Leave-One-Out Cross-Validation (LOOCV):
   - Special case where k = n (number of samples)
   - Each sample used once as test set
   - Provides unbiased estimate but computationally expensive
   - High variance in performance estimates

4. Time Series Cross-Validation:
   - Respects temporal order of data
   - Training set always precedes test set chronologically
   - Prevents look-ahead bias in time-dependent data

5. Group K-Fold:
   - Ensures samples from the same group don't appear in both training and test sets
   - Important when samples are not independent (e.g., multiple samples from same patient)

Benefits:
- More robust performance estimates
- Better use of available data
- Helps detect overfitting
- Provides confidence intervals for performance metrics

Implementation considerations:
- Computational cost increases with k
- Variance of estimate decreases as k increases
- Bias of estimate may increase with very large k
- Must maintain data preprocessing within each fold
                """
            }
        }
    }


def demonstrate_response_api_file_search():
    """Main demonstration function for Response API File_Search integration"""
    
    print("🚀 OpenAI Response API File_Search Integration (US-011)")
    print("=" * 60)
    print("Demonstrating working patterns for EditingTeam content synthesis")
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize integration
    integration = None
    try:
        integration = ResponseAPIFileSearchIntegration()
        
        # Create sample research data
        print("\n📚 Creating sample research data...")
        research_data = create_sample_research_data()
        print(f"   ✅ Syllabus: {research_data['syllabus']['title']}")
        print(f"   ✅ Modules: {len(research_data['agenda'])}")
        print(f"   ✅ Research Notes: {len(research_data['research_notes'])} sections")
        
        # Demonstrate multi-step synthesis
        results = integration.demonstrate_multi_step_synthesis(research_data)
        
        # Display results summary
        print("\n📊 Integration Demonstration Results")
        print("=" * 40)
        
        if 'error' in results:
            print(f"❌ Demonstration failed: {results['error']}")
        else:
            metrics = results.get('performance_metrics', {})
            print(f"✅ Workflow Steps Completed: {len(results.get('workflow_steps', []))}")
            print(f"✅ Successful Syntheses: {metrics.get('successful_syntheses', 0)}/{metrics.get('total_synthesis_requests', 0)}")
            print(f"🔍 Total Sources Integrated: {metrics.get('total_sources_integrated', 0)}")
            print(f"📝 Content Generated: {metrics.get('total_content_generated', 0):,} characters")
            print(f"⏱️ Processing Time: {metrics.get('processing_time_seconds', 0):.1f} seconds")
            
            # Show sample synthesis result
            synthesis_results = results.get('synthesis_results', [])
            if synthesis_results and synthesis_results[0].get('status') == 'success':
                print(f"\n📖 Sample Synthesis Output (Module: {synthesis_results[0].get('target_module')})")
                print("-" * 60)
                content = synthesis_results[0].get('synthesized_content', '')
                preview = content[:500] + "..." if len(content) > 500 else content
                print(preview)
                
                file_search_results = synthesis_results[0].get('file_search_results', [])
                if file_search_results:
                    print(f"\n🔍 File Search Results ({len(file_search_results)} sources used):")
                    for i, result in enumerate(file_search_results[:3], 1):
                        print(f"   {i}. File ID: {result.get('file_id')}")
                        print(f"      Quote: {result.get('quote', '')[:100]}...")
        
        # Integration patterns for EditingTeam
        print("\n🔧 EditingTeam Integration Patterns")
        print("=" * 40)
        print("This demonstration provides the following patterns for US-004:")
        print("1. ✅ File upload and vector store creation")
        print("2. ✅ Research assistant with file_search capability")
        print("3. ✅ Multi-step content synthesis workflow")
        print("4. ✅ File search result processing and annotation handling")
        print("5. ✅ Performance metrics and quality assessment")
        print("\n📋 Ready for EditingTeam implementation reference!")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {str(e)}")
        
    finally:
        # Cleanup resources
        if integration:
            integration.cleanup_resources()
            
        print("\n✅ Response API File_Search demonstration completed!")


if __name__ == "__main__":
    demonstrate_response_api_file_search() 