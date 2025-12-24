## Plan to Add Detailed English Comments

### Overview
I will add comprehensive English comments to the three MainModule.mod files in the ABB robot project, explaining:
- System architecture and component interactions
- Function purposes and workflows
- Variable meanings and usage
- Process flow and decision logic
- Communication protocols

### Files to Modify
1. **T_ROB_L/PROGMOD/MainModule.mod** - Left arm vial handling
2. **T_ROB_R/PROGMOD/MainModule.mod** - Right arm dispensing operations  
3. **T_SOC_COM/PROGMOD/MainModule.mod** - Socket communication

### Implementation Approach
1. **Add module-level comments** at the beginning of each file explaining the component's role
2. **Document all variables** with their purpose, data type, and usage context
3. **Comment each procedure** with:
   - Purpose and functionality
   - Input/output parameters
   - Process flow
   - Collaboration with other components
4. **Explain key logic** within procedures, especially conditional statements and loops
5. **Document coordinate systems** and reference points
6. **Add comments to shared variables** explaining inter-task communication
7. **Maintain code integrity** - no code changes, only additions of comments

### Comment Structure
```
! Module: [Module Name]
! Purpose: [High-level description]
! Collaborates with: [Other tasks/components]

! Variable: [VarName]
! Type: [Data type]
! Purpose: [Detailed explanation]
! Usage: [How/when it's used]

! Procedure: [ProcName]
! Purpose: [What the procedure does]
! Process: [Step-by-step flow]
! Notes: [Additional context or important details]
```

### Expected Outcome
- All code functionality is clearly documented
- System architecture is easy to understand
- Maintenance and future development are facilitated
- No changes to code behavior
- Consistent commenting style across all files