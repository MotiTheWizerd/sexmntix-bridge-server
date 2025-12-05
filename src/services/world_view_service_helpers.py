    def _build_incremental_summary_prompt(
        self,
        new_conversations: List[Dict[str, Any]],
        cached_summary: Optional[str]
    ) -> str:
        """
        Build prompt for incremental summary generation.
        
        If cached_summary exists, asks LLM to append new steps.
        Otherwise, creates summary from scratch.
        """
        # Extract conversation details
        lines = []
        for idx, conv in enumerate(new_conversations, start=1):
            first_text = self._strip_memory_blocks(conv.get("first_text", "") or "")
            last_text = self._strip_memory_blocks(conv.get("last_text", "") or "")
            created_at = conv.get("created_at") or ""
            
            # Create brief summary
            summary = f"User: {first_text[:100]}... | Assistant: {last_text[:100]}..."
            lines.append(f"{idx}. ({created_at}) {summary}")
        
        joined = "\n".join(lines)
        
        if cached_summary:
            return (
                f"You have an existing conversation summary:\n\n{cached_summary}\n\n"
                "Now append these new conversations to the summary. "
                "Continue the numbered list from where it left off. "
                "Format: step number, timestamp, brief description (1-2 sentences). "
                "Focus on: what was discussed, decisions made, actions taken.\n\n"
                f"New conversations:\n{joined}\n\n"
                "Return ONLY the complete updated summary (including previous steps + new steps)."
            )
        else:
            return (
                "Create a chronological step-by-step summary of these conversations. "
                "Format as numbered list with timestamps. "
                "Focus on: what was discussed, decisions made, actions taken. "
                "Keep each step concise (1-2 sentences).\n\n"
                f"Conversations:\n{joined}\n\n"
                "Return the summary:"
            )

    def _compress_conversations_incremental(
        self,
        new_conversations: List[Dict[str, Any]],
        cached_summary: Optional[str]
    ) -> str:
        """
        Compress new conversations and append to cached summary.
        """
        units = []
        start_num = 1
        
        # Parse existing summary to get last step number
        if cached_summary:
            lines = cached_summary.strip().split("\n")
            for line in reversed(lines):
                if line.strip() and line[0].isdigit():
                    try:
                        num = int(line.split(".")[0])
                        start_num = num + 1
                        break
                    except:
                        pass
        
        # Compress new conversations
        for idx, conv in enumerate(new_conversations, start=start_num):
            user_text = self._strip_memory_blocks(conv.get("first_text", "") or "")
            assistant_text = self._strip_memory_blocks(conv.get("last_text", "") or "")
            created_at = conv.get("created_at") or ""
            
            compressed = self.compressor.compress(user_text=user_text, assistant_text=assistant_text)
            unit = compressed.get("semantic_unit", "").strip()
            if unit:
                units.append(f"{idx}. ({created_at}) {unit}")
        
        # Combine with cached summary
        if cached_summary:
            return cached_summary + "\n" + "\n".join(units)
        else:
            return "\n".join(units)
