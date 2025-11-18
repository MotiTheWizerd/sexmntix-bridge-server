"""
Test script to demonstrate the include list None issue
"""

# Simulate the problematic code pattern
include_embeddings = False

# This is what the code currently does - creates a list with None
include_list_bad = ["documents", "metadatas", "embeddings" if include_embeddings else None]
print(f"Bad include list (with None): {include_list_bad}")
print(f"Types: {[type(item) for item in include_list_bad]}")
print(f"Contains None: {None in include_list_bad}")
print()

# This is what it should do - conditionally build the list
include_list_good = ["documents", "metadatas"]
if include_embeddings:
    include_list_good.append("embeddings")
print(f"Good include list (no None): {include_list_good}")
print(f"Types: {[type(item) for item in include_list_good]}")
print(f"Contains None: {None in include_list_good}")
print()

# Test with include_embeddings = True
include_embeddings = True
include_list_bad_true = ["documents", "metadatas", "embeddings" if include_embeddings else None]
print(f"Bad include list (include_embeddings=True): {include_list_bad_true}")

include_list_good_true = ["documents", "metadatas"]
if include_embeddings:
    include_list_good_true.append("embeddings")
print(f"Good include list (include_embeddings=True): {include_list_good_true}")
