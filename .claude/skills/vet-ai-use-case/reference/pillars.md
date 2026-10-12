# Well-Architected pillars for an AI workload

Microsoft's five pillars, applied to both functional and non-functional requirements, plus
Databricks' governance pillar.

- **Reliability**: what happens when the model endpoint is down or out of quota? Timeouts, retry limits, a fallback?
- **Security**: who can see the inputs and answers? Could a prompt injection leak data or take an action?
- **Cost Optimization**: what drives the monthly cost, and is there a budget alert?
- **Operational Excellence**: is every answer traced, is there an eval set, how are versions released and rolled back?
- **Performance Efficiency**: can it handle the busiest minute within the speed target?
- **Data and AI governance**: which data and models may it use, and who grants that access?

A system needs to be "just as reliable" and "just as secure" as it needs to be: note which
gaps are acceptable for a pilot.
