#!/usr/bin/env python3
"""
Augment Milestone E Knowledge Base with Scenario Q&A Pairs from Milestone C

This script:
1. Loads existing Milestone E KB (561 pairs, 16 categories)
2. Extracts scenario Q&A pairs from Milestone C files
3. Augments E's KB with scenario pairs (new categories: job_search_timeline, expense_reduction, gi_bill, etc.)
4. Recreates FAISS embeddings
5. Saves augmented KB for production use

Result: E becomes comprehensive RAG system handling both factual AND scenario questions
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnowledgeBaseAugmentor:
    def __init__(self):
        self.milestone_e_path = Path("d:/Project Atlas/data/milestone_e_knowledge_base.json")
        self.milestone_c_dir = Path("d:/AIT716/Milestone_C")
        
        # Scenario Q&A files to augment with
        self.scenario_files = [
            "expense_reduction_training_50_pairs.json",
            "expense_reduction_real_pairs.json",
            "expense_reduction_ltc_insurance_15_topics.json",
            "expense_reduction_additional_20_topics.json"
        ]
    
    def read_milestone_e_kb(self) -> Dict:
        """Load current Milestone E knowledge base"""
        logger.info(f"Loading Milestone E KB from {self.milestone_e_path}")
        with open(self.milestone_e_path, 'r') as f:
            kb = json.load(f)
        logger.info(f"Loaded {len(kb['pairs'])} pairs from Milestone E")
        return kb
    
    def extract_scenario_pairs(self) -> List[Dict]:
        """Extract all scenario Q&A pairs from Milestone C files"""
        scenario_pairs = []
        
        for scenario_file in self.scenario_files:
            file_path = self.milestone_c_dir / scenario_file
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            
            logger.info(f"Extracting pairs from {scenario_file}")
            try:
                with open(file_path, 'r') as f:
                    pairs = json.load(f)
                
                # Convert Milestone C format to Milestone E format
                for pair in pairs:
                    # Milestone C uses "input_text" and "target_text"
                    # Milestone E uses "question" and "answer"
                    e_format_pair = {
                        "question": pair.get("input_text", ""),
                        "answer": pair.get("target_text", ""),
                        "category": pair.get("category", "scenario"),
                        "topic": pair.get("topic", ""),
                        "source": pair.get("source", "Milestone_C_Scenario_Augmentation")
                    }
                    
                    # Only add if both Q and A are non-empty
                    if e_format_pair["question"] and e_format_pair["answer"]:
                        scenario_pairs.append(e_format_pair)
                
                logger.info(f"  Extracted {len(pairs)} pairs")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {scenario_file}: {e}")
            except Exception as e:
                logger.error(f"Error processing {scenario_file}: {e}")
        
        logger.info(f"Total scenario pairs extracted: {len(scenario_pairs)}")
        return scenario_pairs
    
    def augment_knowledge_base(self, kb: Dict, scenario_pairs: List[Dict]) -> Dict:
        """Merge scenario pairs into Milestone E KB"""
        logger.info("Augmenting knowledge base...")
        
        # Get initial pair count
        initial_count = len(kb['pairs'])
        
        # Add scenario pairs
        kb['pairs'].extend(scenario_pairs)
        
        # Update category distribution
        for pair in scenario_pairs:
            category = pair.get('category', 'scenario')
            if category not in kb['category_distribution']:
                kb['category_distribution'][category] = 0
            kb['category_distribution'][category] += 1
        
        # Update metadata
        final_count = len(kb['pairs'])
        kb['metadata']['kb_size'] = final_count
        kb['metadata']['categories'] = len(kb['category_distribution'])
        kb['metadata']['augmentation_note'] = f"Augmented on 2026-04-08: Added {len(scenario_pairs)} scenario pairs from Milestone C. Now includes both factual Q&A (original 561) and scenario Q&A ({len(scenario_pairs)})."
        kb['metadata']['scenario_pairs_added'] = len(scenario_pairs)
        kb['metadata']['previous_size'] = initial_count
        
        logger.info(f"✅ Knowledge base augmented: {initial_count} → {final_count} pairs")
        logger.info(f"✅ Categories: {len(kb['category_distribution'])} (added {len([k for k in kb['category_distribution'].keys() if k not in ['disability', 'retirement_pay', 'education', 'housing', 'transition', 'timeline', 'insurance', 'tax', 'survivor_benefits', 'family', 'tsp', 'survivor', 'special_pay', 'job_offer', 'healthcare', 'integration']])})")
        
        return kb
    
    def save_augmented_kb(self, kb: Dict) -> None:
        """Save augmented knowledge base"""
        output_path = self.milestone_e_path
        logger.info(f"Saving augmented KB to {output_path}")
        
        with open(output_path, 'w') as f:
            json.dump(kb, f, indent=2)
        
        logger.info(f"✅ Saved {len(kb['pairs'])} pairs to augmented knowledge base")
    
    def print_category_summary(self, kb: Dict) -> None:
        """Print category distribution summary"""
        logger.info("\n📊 Category Distribution after Augmentation:")
        logger.info("-" * 60)
        
        sorted_categories = sorted(
            kb['category_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        total = sum(count for _, count in sorted_categories)
        
        for category, count in sorted_categories:
            percentage = (count / total) * 100
            bar_length = int(percentage / 2)
            bar = "▓" * bar_length + "░" * (50 - bar_length)
            logger.info(f"{category:20s} {count:3d} ({percentage:5.1f}%) {bar}")
        
        logger.info("-" * 60)
        logger.info(f"{'TOTAL':20s} {total:3d} (100.0%)")
    
    def run(self) -> None:
        """Execute full augmentation pipeline"""
        logger.info("🚀 Starting Milestone E Knowledge Base Augmentation")
        logger.info("=" * 60)
        
        # Step 1: Load existing KB
        kb = self.read_milestone_e_kb()
        
        # Step 2: Extract scenario pairs
        scenario_pairs = self.extract_scenario_pairs()
        
        if not scenario_pairs:
            logger.error("❌ No scenario pairs found! Aborting augmentation.")
            return
        
        # Step 3: Augment KB
        augmented_kb = self.augment_knowledge_base(kb, scenario_pairs)
        
        # Step 4: Save augmented KB
        self.save_augmented_kb(augmented_kb)
        
        # Step 5: Print summary
        self.print_category_summary(augmented_kb)
        
        logger.info("\n✅ Augmentation Complete!")
        logger.info(f"Next step: Rebuild FAISS embeddings using augmented KB")
        logger.info("=" * 60)


if __name__ == "__main__":
    augmentor = KnowledgeBaseAugmentor()
    augmentor.run()
