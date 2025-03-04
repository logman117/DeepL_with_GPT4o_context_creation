# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 05:01:24 2025

@author: lyool
"""
import os
import json
import re
import requests
import deepl
from deepl import Formality, ModelType
from openpyxl import load_workbook

# =============================================================================
# Configuration
# =============================================================================
# Use environment variables if available, otherwise use the provided keys
DEEPL_API_KEY = os.environ.get("DEEPL_API_KEY", "YOUR_DEEPL_API_KEY")
WORKING_DIR = os.getcwd()

# Azure OpenAI API configuration
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "YOUR_AZURE_OPEN_AI_ENDPOINT_LINK")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "YOUR_AZURE_OPEN_AI_KEY")
AZURE_API_VERSION = "2024-08-01-preview"
AZURE_MODEL_NAME = "gpt-4o"

# Azure OpenAI endpoint for chat completions
AZURE_CHAT_ENDPOINT = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_MODEL_NAME}/chat/completions?api-version={AZURE_API_VERSION}"

DEFAULT_FORMALITY = Formality.MORE
DEFAULT_MODEL_TYPE = ModelType.PREFER_QUALITY_OPTIMIZED
PRESERVE_FORMATTING = True

translator = deepl.Translator(DEEPL_API_KEY)

# Context cache to store generated contexts
CONTEXT_CACHE = {}
# Description cache to avoid regenerating descriptions
DESCRIPTION_CACHE = {}

# =============================================================================
# File-Level Descriptions for UI Files
# =============================================================================
FILE_DESCRIPTIONS = {
    "component.json": "This file contains UI component labels, such as buttons and input placeholders for the touchscreen interface of the machine.",
    "dynamic.json": "This file holds dynamic configuration texts and settings descriptions for various cleaning modes and machine operations.",
    "language.json": "This file lists language names used for the UI language selection on the machine.",
    "notification.json": "This file contains notification messages, error alerts, and status updates for the machine interface.",
    "screen.json": "This file comprises screen titles, instructions, and button labels for various sections of the touchscreen interface.",
    "unit.json": "This file defines measurement units and dynamic templates used across the machine's UI."
}

# =============================================================================
# Azure OpenAI Chat API Context Generation Function with File-Level Metadata
# =============================================================================
def generate_context_for_string(key_path: str, original_text: str, file_name: str) -> str:
    """
    Generate a context string using Azure OpenAI's Chat Completion endpoint.
    The API call includes the file description, key path, and original text to produce a context.
    This function uses the GPT-4o model deployed on Azure.
    """
    # Create a unique cache key
    cache_key = f"{file_name}|{key_path}|{original_text}"
    
    # Check if the context is already in the cache
    if cache_key in CONTEXT_CACHE:
        return CONTEXT_CACHE[cache_key]
    
    # Skip context generation for very short texts or empty keys
    if not key_path or not original_text or len(original_text.strip()) < 2:
        context = f"Context for UI element: {key_path}"
        CONTEXT_CACHE[cache_key] = context
        return context
        
    file_description = FILE_DESCRIPTIONS.get(file_name, "UI text for the machine.")
    
    # Extract parent keys to provide better context
    key_parts = key_path.split('.')
    parent_context = " > ".join(key_parts)
    
    prompt = (
        f"Generate a translation context for a UI string from a machine touchscreen interface.\n"
        f"File: '{file_name}'\n"
        f"File Description: '{file_description}'\n"
        f"Key path: '{key_path}'\n"
        f"Key hierarchy: '{parent_context}'\n"
        f"Original text: '{original_text}'\n\n"
        f"Guidelines: Provide a concise description indicating where and how the text is used, its purpose, "
        f"and any potential ambiguities. For example, if it is a button label, mention that. "
        f"For simple language name like 'Portuguese (Brazil)', indicate it's a language selection option.\n"
        f"Now, generate the context."
    )
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates precise UI translation contexts."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    try:
        # Increase timeout to 30 seconds to help avoid read timeouts.
        response = requests.post(AZURE_CHAT_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        context = data["choices"][0]["message"]["content"].strip()
        if not context:
            context = f"Context for UI element: {key_path}"
        
        # Store the context in the cache
        CONTEXT_CACHE[cache_key] = context
        return context
    except Exception as e:
        print(f"Warning: Error generating context for {key_path}: {e}")
        # Return a basic context as fallback
        context = f"Context for UI element: {key_path} in {file_name}"
        CONTEXT_CACHE[cache_key] = context
        return context

# =============================================================================
# Generate Missing Descriptions Function
# =============================================================================
def generate_missing_description(key_path: str, data: dict, file_name: str) -> str:
    """
    Generates a missing description field using Azure OpenAI API based on
    surrounding context in the data structure.
    """
    # Check if this description is already in the cache
    cache_key = f"{file_name}|{key_path}"
    if cache_key in DESCRIPTION_CACHE:
        return DESCRIPTION_CACHE[cache_key]
    
    # Skip processing if key_path is empty
    if not key_path:
        description = "Controls settings for the machine"
        DESCRIPTION_CACHE[cache_key] = description
        return description
    
    # Get the parent key
    parent_key = key_path.split('.')[-1] if '.' in key_path else key_path
    
    # Extract all available context from the data
    context_info = {}
    
    # Add name field if available
    if isinstance(data, dict):
        if "name" in data:
            context_info["name"] = data["name"]
        if "shortName" in data:
            context_info["shortName"] = data["shortName"]
    
    # Add sibling descriptions for context
    sibling_descriptions = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                if "description" in value and value["description"]:
                    name_value = value.get("name", key)
                    sibling_descriptions.append(f"{name_value}: {value['description']}")
                    
    prompt = (
        f"Generate a concise description for a missing field in a cleaning machine UI.\n\n"
        f"Field key path: {key_path}\n"
        f"Field name: {context_info.get('name', parent_key)}\n"
    )
    
    if context_info.get("shortName"):
        prompt += f"Short name: {context_info['shortName']}\n"
    
    if sibling_descriptions:
        prompt += "\nRelated fields for context:\n" + "\n".join(sibling_descriptions) + "\n\n"
        
    prompt += (
        f"Based on this information, generate a brief, clear description for the '{parent_key}' setting "
        f"that explains what this control does on the cleaning machine. "
        f"Keep it concise (under 100 characters) and focused on user understanding."
    )
    
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that generates concise UI descriptions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(AZURE_CHAT_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        description = data["choices"][0]["message"]["content"].strip()
        print(f"  Generated description for {key_path}: {description}")
        
        # Cache the result
        DESCRIPTION_CACHE[cache_key] = description
        return description
    except Exception as e:
        print(f"  Error generating description for {key_path}: {e}")
        description = "Controls settings for the machine"  # Fallback description
        DESCRIPTION_CACHE[cache_key] = description
        return description

# =============================================================================
# Preprocess JSON to Fill Missing Descriptions
# =============================================================================
def preprocess_json_with_descriptions(data, key_prefix: str, file_name: str):
    """
    Recursively traverses JSON and fills in empty description fields
    """
    if isinstance(data, dict):
        updated_data = {}
        for key, value in data.items():
            full_key = f"{key_prefix}.{key}" if key_prefix else key
            
            # Check if this is a description field that's empty
            if key == "description" and (value is None or value == ""):
                # Get parent object to use for context
                parent_dict = data
                updated_data[key] = generate_missing_description(key_prefix, parent_dict, file_name)
            else:
                # Recursively process the value
                updated_data[key] = preprocess_json_with_descriptions(value, full_key, file_name)
        return updated_data
    elif isinstance(data, list):
        return [preprocess_json_with_descriptions(item, key_prefix, file_name) for item in data]
    else:
        return data

# =============================================================================
# Context Generation Pass: Generate and store contexts for all strings in JSON
# =============================================================================
def generate_contexts_for_json(data, key_prefix: str, file_name: str, contexts_dict=None):
    """
    First pass: recursively traverse the JSON, generate contexts for all strings,
    and store them in a dictionary.
    """
    if contexts_dict is None:
        contexts_dict = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{key_prefix}.{key}" if key_prefix else key
            generate_contexts_for_json(value, full_key, file_name, contexts_dict)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            generate_contexts_for_json(item, f"{key_prefix}[{i}]", file_name, contexts_dict)
    elif isinstance(data, str) and data.strip():
        # Generate context for non-empty strings
        generate_context_for_string(key_prefix, data, file_name)
    
    return contexts_dict

# =============================================================================
# Translation Phase: Translate strings using pre-generated contexts
# =============================================================================
def translate_json(data, key_prefix: str, file_name: str, target_lang_code: str, supports_formality: bool):
    """
    Second pass: recursively traverse the JSON data and translate strings using
    the contexts that were previously generated and stored in CONTEXT_CACHE.
    """
    if isinstance(data, dict):
        translated_dict = {}
        for key, value in data.items():
            full_key = f"{key_prefix}.{key}" if key_prefix else key
            translated_dict[key] = translate_json(value, full_key, file_name, target_lang_code, supports_formality)
        return translated_dict
    elif isinstance(data, list):
        return [translate_json(item, f"{key_prefix}[{i}]", file_name, target_lang_code, supports_formality) 
                for i, item in enumerate(data)]
    elif isinstance(data, str):
        # Skip translation for empty strings
        if not data.strip():
            return data
            
        try:
            # Retrieve the previously generated context
            cache_key = f"{file_name}|{key_prefix}|{data}"
            context_for_string = CONTEXT_CACHE.get(cache_key, f"Context for UI element: {key_prefix}")
            
            # Log what we're translating
            print(f"  Translating: '{data}' with context: '{context_for_string}'")
            
            result = translator.translate_text(
                data,
                source_lang="EN",  # Assuming the source language is English
                target_lang=target_lang_code,
                context=context_for_string,
                formality=DEFAULT_FORMALITY if supports_formality else None,
                model_type=DEFAULT_MODEL_TYPE,
                preserve_formatting=PRESERVE_FORMATTING
            )
            return result.text
        except Exception as e:
            print(f"  Warning: Translation error at {key_prefix} in {file_name}: {e}")
            # Return original string on error to allow the process to continue
            return data
    else:
        # For numbers, booleans, etc., return as is.
        return data

# =============================================================================
# Process All JSON Files in the Working Directory
# =============================================================================
def main():
    # List all JSON files (excluding non-JSON files)
    json_files = [
        f for f in os.listdir(WORKING_DIR)
        if f.endswith(".json") and os.path.isfile(os.path.join(WORKING_DIR, f))
    ]
    
    if not json_files:
        print(f"No JSON files found in {WORKING_DIR}")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    try:
        # Validate Azure OpenAI API credentials with a simple test call
        test_prompt = "Test connection to Azure OpenAI"
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        payload = {
            "messages": [
                {"role": "user", "content": test_prompt}
            ],
            "temperature": 0.0
        }
        
        print(f"Testing Azure OpenAI connection to: {AZURE_CHAT_ENDPOINT}")
        response = requests.post(AZURE_CHAT_ENDPOINT, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        print("✓ Azure OpenAI connection successful")
        
        # Test DeepL connection
        target_languages = translator.get_target_languages()
        print(f"✓ DeepL connection successful - Retrieved {len(target_languages)} target languages")
    except Exception as e:
        print(f"Error testing API connections: {e}")
        return
    
    # =============================================================================
    # First pass: Preprocess all JSON files and generate contexts
    # =============================================================================
    print("\n=== Phase 1: Preprocessing JSON files and generating contexts ===")
    
    # Dictionary to store preprocessed JSON data for each file
    preprocessed_json_data = {}
    
    for json_filename in json_files:
        json_path = os.path.join(WORKING_DIR, json_filename)
        print(f"Processing file: {json_filename}")
        
        try:
            with open(json_path, "r", encoding="utf-8") as infile:
                try:
                    original_data = json.load(infile)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON in {json_filename}: {e}")
                    continue
            
            # Preprocess to fill in any missing descriptions for all JSON files
            # Skip preprocessing for language.json as it has a very simple structure
            if json_filename != "language.json":
                print(f"Preprocessing {json_filename} to generate missing descriptions...")
                original_data = preprocess_json_with_descriptions(original_data, "", json_filename)
            
            # Store the preprocessed data
            preprocessed_json_data[json_filename] = original_data
            
            # Generate contexts for all strings in the JSON file
            print(f"Generating contexts for all strings in {json_filename}...")
            generate_contexts_for_json(original_data, "", json_filename)
            
            print(f"✓ Preprocessed {json_filename} and generated contexts")
        
        except Exception as e:
            print(f"✗ Error preprocessing {json_filename}: {e}")
    
    print(f"Generated contexts for {len(CONTEXT_CACHE)} unique strings")
    
    # =============================================================================
    # Second pass: Translate the JSON files for each target language
    # =============================================================================
    print("\n=== Phase 2: Translating JSON files for each target language ===")
    
    for lang_obj in target_languages:
        target_lang_code = lang_obj.code  # e.g., "DE", "FR", "PT-BR", etc.
        supports_formality = lang_obj.supports_formality
        
        print(f"\nProcessing language: {target_lang_code} (Formality supported: {supports_formality})")
        
        # Create folder for the target language (using lower-case folder name for 2-letter codes)
        folder_name = target_lang_code.lower() if len(target_lang_code) == 2 else target_lang_code
        folder_path = os.path.join(WORKING_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        for json_filename, original_data in preprocessed_json_data.items():
            print(f"  Translating file: {json_filename} to {target_lang_code}")
            
            try:
                # Translate the JSON data recursively using pre-generated contexts
                translated_data = translate_json(original_data, key_prefix="", file_name=json_filename,
                                               target_lang_code=target_lang_code, supports_formality=supports_formality)
                
                # Write the translated JSON back into the target language folder
                output_filepath = os.path.join(folder_path, json_filename)
                with open(output_filepath, "w", encoding="utf-8") as outfile:
                    json.dump(translated_data, outfile, ensure_ascii=False, indent=2)
                
                print(f"  ✓ Created translation for '{json_filename}' in {target_lang_code} folder '{folder_name}'.")
            except Exception as e:
                print(f"  ✗ Error translating {json_filename} for {target_lang_code}: {e}")
    
    print(f"\nAll translations complete. Used {len(CONTEXT_CACHE)} cached contexts across all languages.")

if __name__ == "__main__":
    main()
