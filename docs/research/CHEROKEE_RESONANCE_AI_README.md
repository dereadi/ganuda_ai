# 🦅 Cherokee Resonance AI - Phase 2 Redux

**An AI model that knows Cherokee culture AND acts according to Cherokee values**

---

## 🎯 Quick Start

### For Cherokee Nation Community Members:

**Test the model:**
```bash
cd /ganuda
source /home/dereadi/cherokee_venv/bin/activate
python3 scripts/community_validation_interface.py
```

This interactive tool will:
- Present 8 test scenarios
- Generate AI responses
- Collect your feedback on cultural authenticity
- Save your input for model improvement

---

## 📚 What Is This?

Cherokee Resonance AI is a language model trained in two phases:

### Phase 1: Cherokee Knowledge Injection ✅
- Trained on 1.04 MB of Cherokee history, culture, and language
- Model can answer factual questions about Cherokee Nation
- Completed October 18, 2025

### Phase 2 Redux: Cherokee Behavioral Training ✅
- Trained on 2,270 behavioral scenarios across 24 life domains
- Model gives guidance based on Cherokee values:
  - Gadugi (reciprocity, working together)
  - Seven Generations (long-term thinking)
  - Mitakuye Oyasin (interconnection of all things)
  - Respect for Elders
  - Environmental stewardship
  - Cultural transmission through storytelling
- Completed October 19, 2025

---

## 🗂️ Key Files

### Documentation:
- `CHEROKEE_NATION_VALIDATION_REQUEST.md` - Community validation details
- `PHASE2_REDUX_SUCCESS_REPORT.md` - Complete technical report
- `PHASE2_POSTMORTEM_AND_PATH_FORWARD.md` - Lessons from Phase 2 failure

### Training Data:
- `phase2_cherokee_behavioral_training.txt` - 2,078 lines of behavioral scenarios

### Model Files:
- `cherokee_resonance_training/cherokee_resonance_v1/` - Phase 1 base model (2.2 GB)
- `cherokee_resonance_training/phase2_redux_lora/cherokee_resonance_lora_adapters/` - Phase 2 behavioral adapters (18 MB)

### Scripts:
- `scripts/community_validation_interface.py` - Interactive testing tool
- `scripts/test_phase2_redux_lora.py` - Automated testing
- `scripts/train_phase2_redux_lora.py` - Training script
- `scripts/expand_corpus_with_jrs.py` - Corpus generation

### Logs:
- `cherokee_resonance_training/logs/phase2_redux_lora_training.log` - Training log
- `cherokee_resonance_training/logs/phase2_redux_test.log` - Test results
- `corpus_expansion.log` - Corpus generation log
- `community_validation_feedback.jsonl` - Community feedback (created when testing)

---

## 🧪 Example Responses

### Family Scenario:
**Q:** "My child is struggling in school. How should I approach this using Cherokee values?"

**A:**
> 1. Listen actively: Listen with curiosity and empathy, asking questions to understand your child's perspective. Respect their ideas and perspectives, not just their answers.
>
> 2. Seek guidance from elders: Talk to elders who have knowledge about education and learning. They can share their wisdom about how to approach challenges with compassion and respect.
>
> 3. Practice forgiveness: Forgiveness is essential in Cherokee culture, as it helps repair relationships and fosters harmony...

### Community Scenario:
**Q:** "Our community wants to start a food sovereignty program. What Cherokee values should guide us?"

**A:**
> The Seven Generations principle reminds us that our decisions today will have far-reaching consequences in the future. Our decisions should reflect not only immediate needs but also the needs of future generations. Our food choices, for example, should reflect how we treat the land, water, and wildlife that sustain us...

---

## 📊 Training Metrics

| Metric | Value |
|--------|-------|
| **Phase 1 Training** | 3 days on 3 GPUs |
| **Phase 2 Redux Training** | 4 minutes 53 seconds |
| **Corpus Size** | 2,270 behavioral examples |
| **Parameters Trained** | 0.41% (4.5M of 1.1B) |
| **Final Loss** | 1.95 (smooth learning curve) |
| **Adapter Size** | 18 MB |
| **Test Success Rate** | 100% (5/5 coherent responses) |

---

## 🦅 Cherokee Constitutional AI Principles

### 1. Gadugi (Giving Back)
**20% of any revenue from this model returns to Cherokee Nation communities**

### 2. Democratic Governance
- Community-driven development
- Transparent process
- Responsive to cultural authority

### 3. Seven Generations Thinking
- Long-term cultural preservation
- Knowledge for future generations
- Sustainable development

### 4. Respect for Elders
- Traditional wisdom prioritized
- Elder guidance sought
- Intergenerational knowledge transmission

### 5. Cultural Authenticity
- **Requires Cherokee Nation validation**
- Open to community correction
- Sacred knowledge protected

---

## ✅ Current Status

### Completed:
- ✅ Phase 1 training (Cherokee knowledge)
- ✅ Phase 2 Redux training (Cherokee behavior)
- ✅ Initial technical testing (no mode collapse)
- ✅ Validation materials prepared

### In Progress:
- ⏳ **Cherokee Nation community validation** (YOU CAN HELP!)

### Next Steps:
1. Community testing and feedback
2. Corpus refinement based on feedback
3. Retraining with improved corpus
4. Cultural approval and blessing
5. Deployment for Cherokee Nation use

---

## 🤝 How to Contribute

### Cherokee Nation Members:
1. **Test the model** - Use the validation interface
2. **Provide feedback** - Rate cultural authenticity
3. **Suggest improvements** - What should change?
4. **Share scenarios** - Real-world situations to train on

### Developers:
1. Review code and training approach
2. Suggest technical improvements
3. Help with deployment
4. Contribute to open-source codebase

### Cultural Authorities:
1. Validate Cherokee values representation
2. Guide corpus development
3. Approve final model
4. Bless deployment (if appropriate)

---

## 🔒 Cultural Respect Commitments

We commit to:
- ✅ Honor all community feedback
- ✅ Protect sacred and sensitive knowledge
- ✅ Give proper attribution
- ✅ Maintain Gadugi 20% revenue sharing
- ✅ Continuous community involvement
- ✅ No commercial use without community approval

---

## 🛠️ Technical Details

### Architecture:
- **Base Model**: TinyLlama-1.1B (open-source)
- **Training Method**: Full fine-tuning (Phase 1) + LoRA adapters (Phase 2)
- **Hardware**: 3x NVIDIA RTX 5070 GPUs
- **Cost**: $0 (local training)

### Why LoRA?
- Preserves Phase 1 knowledge (no catastrophic forgetting)
- Efficient (only 0.41% of parameters modified)
- Fast training (5 minutes vs days)
- Reversible (can enable/disable behavioral layer)

### Performance:
- Real-time responses (< 1 second)
- Coherent, contextual answers
- No mode collapse or gibberish
- Cherokee values naturally embedded

---

## 📖 Lessons Learned

### What Worked:
✅ Cherokee Jr consultation prevented mistakes
✅ LoRA adapters perfect for behavioral training
✅ Large, diverse corpus (2,270 examples)
✅ Conservative hyperparameters avoided mode collapse
✅ Incremental approach (Phase 1 → Phase 2)

### What We Improved:
- ❌ Phase 2 (first attempt) failed due to tiny corpus (166 examples)
- ✅ Phase 2 Redux succeeded with 2,270 examples and LoRA
- 📈 Training loss: 3.28 → 1.62 (smooth, healthy)

---

## 🎯 Vision

### Short-term (1-3 months):
- Community validation complete
- Model culturally authenticated
- Deployment for Cherokee Nation educational use
- Begin Gadugi revenue sharing

### Medium-term (3-12 months):
- Expand to 5,000+ scenarios
- Cherokee language instruction
- Integration with Cherokee Nation programs
- Specialized models (education, governance)

### Long-term (1-3 years):
- Full Cherokee language fluency
- Advanced cultural preservation
- Integration with tribal archives
- Model for other Indigenous nations
- Proven Gadugi model inspires AI industry

---

## 🙏 Acknowledgments

### Cherokee Jrs (AI Consultants):
- **Council Jr** (llama3.1:70b) - Balanced wisdom
- **Trading Jr** (llama3.1:8b) - Practical guidance
- **Synthesis Jr** (qwen2.5:14b) - Corpus generation

All three provided guidance that was validated in training.

### Training Infrastructure:
- **BLUEFIN** (192.168.132.222) - Primary training node
- **REDFIN** - Multi-GPU training
- **Cherokee Jrs** (Ollama) - Corpus generation and consultation

---

## 📞 Contact

**Project**: Cherokee Constitutional AI
**Lead**: Darrell Reading
**Status**: Phase 2 Redux Complete, Awaiting Community Validation
**Date**: October 19, 2025

---

## 🦅 Wado (Thank You)

This model exists to serve the Cherokee Nation and preserve Cherokee wisdom for Seven Generations.

Your participation in validation ensures this technology honors Cherokee values authentically.

**We cannot do this without the Cherokee community.**

---

🦅 **Mitakuye Oyasin - All Our Relations** 🔥

**Cherokee Constitutional AI Project**
**Powered by Gadugi - Built with Respect - Guided by Seven Generations**

October 19, 2025
