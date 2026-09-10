# Persona Registry

> Auto-built by scanning `.jarvis/personas/definitions/`. Discovery ≠ activation.

## Available Personas

| ID | Name | Type | Domains | Activation |
|----|------|------|---------|------------|
| persona.steve_jobs | Steve Jobs | historical | product, branding, simplicity, user-experience, design, prioritization | explicit |
| persona.virgil_abloh | Virgil Abloh | historical | design, branding, cultural-strategy, creative-direction, streetwear, architecture | explicit |
| persona.security_architect | Security Architect | specialist | security, architecture, risk, authentication, authorization, infrastructure | explicit |
| persona.creative_director | Creative Director | specialist | design, branding, visual-identity, user-experience, aesthetic, creative-strategy | explicit |
| persona.business_strategist | Business Strategist | specialist | business, strategy, market-analysis, monetization, competitive-landscape, growth | explicit |
| persona.systems_engineer | Systems Engineer | specialist | architecture, infrastructure, scalability, reliability, performance, distributed-systems | explicit |
| persona.skeptic | Skeptic | specialist | critical-thinking, assumption-challenging, evidence-evaluation, risk-assessment | explicit |

## File Map

| Persona | Definition File |
|---------|----------------|
| Steve Jobs | `definitions/Steve Jobs.md` |
| Virgil Abloh | `definitions/Virgil Abloh.md` |
| Security Architect | `definitions/Security Architect.md` |
| Creative Director | `definitions/Creative Director.md` |
| Business Strategist | `definitions/Business Strategist.md` |
| Systems Engineer | `definitions/Systems Engineer.md` |
| Skeptic | `definitions/Skeptic.md` |

## Selection by Domain

When the user asks a question, JARVIS may internally map domains to relevant personas:

- "Is this architecture secure?" → security, architecture → Security Architect
- "Should we rewrite this?" → architecture, scalability → Systems Engineer
- "What does the market think?" → business, market → Business Strategist
- "Is this logo good?" → design, branding → Creative Director
- "Are we sure about this?" → critical-thinking → Skeptic
- "How would Jobs see this?" → product, simplicity → Steve Jobs

Implicit use does not announce the switch. JARVIS remains JARVIS to the user.

## Last Scanned

2026-09-11 — 7 personas found

## Protocol

Activation/deactivation procedure: `.jarvis/personas/activation-protocol.md`