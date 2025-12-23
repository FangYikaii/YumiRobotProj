MODULE MainModule
    ! ==========================================================================
    ! T_ROB_R - Right Arm Module for Yumi Robot
    ! Main function: High-precision material dispensing system
    ! Features: Material scooping, shaking control, weight detection, error handling
    ! ==========================================================================

    ! ----------------------------
    ! Tool and Work Object Data
    ! ----------------------------
    ! Tool configuration for right arm gripper
    PERS tooldata tool1:=[TRUE,[[0,0,0],[1,0,0,0]],[0.215,[8.7,12.3,49.2],[1,0,0,0],0.00017,0.0002,0.0008]];
    
    ! Calibrated workpiece coordinate system for robot positioning
    PERS wobjdata wobjCalibR:=[FALSE,TRUE,"",[[317.006,-224.141,0.857552],[0.999786,-0.000786004,-0.00371968,0.0203487]],[[0,0,0],[1,0,0,0]]];

    ! ----------------------------
    ! Target Positions
    ! ----------------------------
    ! Various target positions for right arm movements
    CONST robtarget p1:=[[320.44,-148.12,194.63],[0.0266083,0.0600672,-0.997753,0.0131502],[1,0,-1,5],[129.395,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p11:=[[454.17,-167.92,253.07],[0.00400204,-0.0784794,0.995596,-0.0511276],[1,1,-1,5],[139.168,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp21:=[[288.07,-203.34,242.71],[0.0134946,0.0347027,0.998353,0.043644],[1,0,-1,5],[138.563,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp31:=[[288.07,-203.34,242.71],[0.0134955,0.0347039,0.998353,0.0436434],[1,0,-1,5],[138.563,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp12:=[[442.59,-153.43,203.45],[0.0206066,0.0565573,-0.998082,0.0144237],[1,1,-1,5],[141.968,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp23:=[[279.96,-126.14,228.69],[0.060459,0.0439555,-0.99699,-0.0205784],[1,0,-1,5],[137.197,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp33:=[[338.22,-158.88,201.52],[0.0157719,0.027297,0.997662,-0.0606435],[1,0,-1,5],[136.943,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp22:=[[423.37,-89.76,217.40],[0.00355343,-0.175019,0.982732,0.0599475],[1,1,-1,5],[144.754,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget dyp32:=[[336.18,-128.23,181.82],[9.66128E-05,-0.41719,0.908818,-0.0018713],[1,0,-1,5],[134.863,9E+09,9E+09,9E+09,9E+09,9E+09]];
    
    ! ----------------------------
    ! Speed and Force Settings
    ! ----------------------------
    ! Speed configuration for robot movements
    CONST speeddata speed1:=[3000,1000,10000,2000];
    CONST speeddata v_move := v500;       ! General movement speed (500mm/s)
    CONST zonedata z_move := z10;         ! General zone size (10mm)
    
    ! ----------------------------
    ! Persistent Variables (Shared)
    ! ----------------------------
    PERS num recvReading:=9.735;           ! Received weight reading from scale
    PERS num recvTargetWeight;              ! Received target weight from external system
    PERS bool isClientConnected;            ! Client connection status
    PERS bool isLeftFinish;                 ! Left arm completion flag
    PERS num weightHistory{15};             ! Weight history array for blocking detection
    PERS num resultArray{5};                ! Result array: [precision, difference, target_weight, sample_num, default_state]
    
    ! ----------------------------
    ! Persistent Variables (Module-Specific)
    ! ----------------------------
    PERS bool isVialWeightReady:=false;     ! Vial weight ready flag
    PERS bool isHopperBack:=False;           ! Hopper back position flag
    PERS bool isDispensingFinish:=FAlse;     ! Dispensing process completion flag
    PERS bool isVialPut:=FALSE;              ! Vial placed flag
    PERS bool isVialBack:=FALSE;             ! Vial returned flag
    PERS bool isHopperPickDone:=FALSE;       ! Hopper pick completion flag
    PERS bool isSendResult:=False;           ! Send result flag
    PERS bool isRecvStable:=FALSE;           ! Weight reading stable flag
    PERS bool isInitialVialPut:=FALSE;      ! Initial vial placement flag
    PERS bool isDataLoadDone:=FALSE;        ! Data loading completion flag
    PERS bool isSampleLStart:=FALSE;         ! Left sample start flag
    PERS bool isHopperBackStart:=FALSE;     ! Hopper back start flag
    PERS num overError:=0;                 ! Over error flag
    PERS bool isSend:=FALSE;                  ! Send message flag
    PERS num vialWeight;                   ! Vial weight
    
    ! ----------------------------
    ! Temporary Variables
    ! ----------------------------
    VAR bool isBlocking:=FALSE;               ! Blocking detection flag
    VAR num targetWeight;                   ! Current target weight
    VAR num weightDifference1;                    ! Weight difference measurement 1
    VAR num weightDifference2;                    ! Weight difference measurement 2
    VAR num weightDifference3;                    ! Weight difference measurement 3
    VAR num weightDifference4;                    ! Weight difference measurement 4
    VAR num weightDifference5;                    ! Weight difference measurement 5
    VAR num averageWeightDifference;                     ! Average weight difference
    VAR num jointAngle;                          ! Joint 7 angle
    VAR bool isOperationEnabled:=TRUE;                  ! Operation mode switch
    VAR num previousWeightReading;                             ! Previous weight reading
    VAR num currentWeightReading;                             ! Current weight reading  
    VAR num weightChange;                           ! Weight change (r2-r1)
    VAR num noDroppingThreshold;                     ! No dropping threshold
    VAR bool isSmallSpoonActive:=FALSE;                  ! Small spoon active flag
    VAR bool isMediumSpoonActive:=FALSE;                 ! Medium spoon active flag
    VAR num retryCount;                    ! Retry counter for loops
    
    ! ==========================================================================
    ! Main Program Entry
    ! ==========================================================================
    PROC main()
        ! Initialization phase
        initializeRightStart;               ! Pre-dispensing initialization
        
        ! Preparation phase
        placeVialInScale;                   ! Place vial in scale
        WaitUntil isHopperPickDone;         ! Wait for hopper pick completion
        
        ! Material dispensing phase
        agitateMaterials;                   ! Mix materials
        
        ! Select appropriate spoon based on target weight
        IF targetWeight >= 0.8 THEN
            largeSpoonOperation;            ! Large spoon operation
        ELSE
            mediumSpoonOperation;           ! Medium spoon operation
            smallSpoonOperation;            ! Small spoon operation
        ENDIF
        
        ! Result processing phase
        calculateDispensingResults;         ! Calculate dispensing results
        
        ! Completion phase
        isHopperBackStart:=TRUE;            ! Start hopper return sequence
        WaitUntil isHopperBack;             ! Wait for hopper to return
        completeOperation;                  ! Complete operation, return vial, close scale door
        
        ! Synchronization with left arm
        WaitUntil isLeftFinish;             ! Wait for left arm to complete
    ENDPROC
    
    ! ==========================================================================
    ! Initialization Procedures
    ! ==========================================================================
    
    ! Initialize system state variables
    PROC initializeSystemState()
        ! Reset all system flags to initial state
        isVialWeightReady:=false;
        isHopperBack:=False;
        isDispensingFinish:=FAlse;
        isVialPut:=FALSE;
        isVialBack:=FALSE;
        isHopperPickDone:=FALSE;
        isSendResult:=False;
        isRecvStable:=FALSE;
        isInitialVialPut:=FALSE;
        isBlocking:=FALSE;
        isDataLoadDone:=FALSE;
        isSampleLStart:=FALSE;
        isOperationEnabled := TRUE;
        isSmallSpoonActive:=FALSE;
        isMediumSpoonActive:=FALSE;
        isHopperBackStart:=FALSE;
        weightChange:=2;
        overError:=0;
        isSend:=FALSE;
    ENDPROC
    
    ! Pre-dispensing initialization and data loading
    PROC initializeRightStart()
        initializeSystemState();            ! Reset all system states
        ! Additional initialization steps would go here
        ! such as loading calibration data, checking sensors, etc.
    ENDPROC
    
    ! ==========================================================================
    ! Material Handling Procedures
    ! ==========================================================================
    
    ! Place vial inside scale
    PROC placeVialInScale()
        ! Implementation for placing vial in scale
        ! This would include robot movements to pick and place the vial
    ENDPROC
    
    ! Agitate/mix materials
    PROC agitateMaterials()
        ! Implementation for agitating/mixing materials
        ! This would include robot movements to mix the material
    ENDPROC
    
    ! Complete operation and return vial
    PROC completeOperation()
        ! Implementation for completing the operation
        ! This would include returning the vial, closing the scale door, etc.
    ENDPROC
    
    ! ==========================================================================
    ! Spoon Operation Procedures
    ! ==========================================================================
    
    ! Large spoon operation
    PROC largeSpoonOperation()
        IF targetWeight >= 0.8 THEN
            pickLargeSpoon;                 ! Pick up large spoon
            shakeLargeSpoon;                ! Shake large spoon to remove excess material
            calculateDifference;            ! Calculate initial weight difference
            
            retryCount := 0;                ! Initialize retry counter
            ! Continue scooping until difference <= 0.8g or max retries reached
            WHILE averageWeightDifference > 0.8 AND retryCount < 50 DO
                g_SetForce 100;             ! Set gripper force to 100N
                scoopLarge;                 ! Scoop material with large spoon
                shakeLargeSpoon;            ! Shake spoon to remove excess
                calculateDifference;        ! Recalculate weight difference
                retryCount := retryCount + 1;  ! Increment retry counter
            ENDWHILE
            
            ! Handle max retry case
            IF retryCount >= 50 THEN
                overError := 2;             ! Set timeout error
                isSend := TRUE;
            ENDIF
            
            returnLargeSpoon;               ! Return large spoon to storage
        ENDIF
    ENDPROC
    
    ! Medium spoon operation
    PROC mediumSpoonOperation()
        isMediumSpoonActive:=TRUE;          ! Set medium spoon active flag
        calculateDifference;                ! Calculate initial weight difference
        
        IF averageWeightDifference > 0.1 THEN
            pickMediumSpoon;                ! Pick up medium spoon
            
            retryCount := 0;                ! Initialize retry counter
            ! Continue scooping until difference < 0.1g or max retries reached
            WHILE averageWeightDifference >= 0.1 AND retryCount < 50 DO
                previousWeightReading:=recvReading; ! Record current weight reading
                g_SetForce 100;             ! Set gripper force to 100N
                calculateDifference;        ! Calculate weight difference
                shakeMediumSpoon;           ! Shake medium spoon (parameters from Python)
                
                ! Dynamic wait time based on difference (1-4 seconds)
                WaitTime MAX(1, MIN(4, 1 + averageWeightDifference*2));
                
                currentWeightReading:=recvReading;  ! Record new weight reading
                loadNoDroppingThreshold;    ! Calculate no dropping threshold
                
                weightChange:=currentWeightReading-previousWeightReading; ! Calculate weight change
                TPWrite "weightChange medium: " \Num:=weightChange; ! Display weight change
                
                ! Only scoop if weight change is below no dropping threshold
                IF weightChange < noDroppingThreshold THEN
                    scoopMedium;            ! Scoop material with medium spoon
                ENDIF
                
                ! Dynamic wait time for stabilization
                WaitTime MAX(1, MIN(4, 1 + averageWeightDifference*2));
                calculateDifference;        ! Recalculate weight difference
                retryCount := retryCount + 1;  ! Increment retry counter
            ENDWHILE
            
            ! Handle max retry case
            IF retryCount >= 50 THEN
                overError := 2;             ! Set timeout error
                isSend := TRUE;
            ENDIF
            
            returnMediumSpoon;              ! Return medium spoon to storage (fixed typo)
        ENDIF
        isMediumSpoonActive:=false;         ! Clear medium spoon active flag
    ENDPROC
    
    ! Small spoon operation
    PROC smallSpoonOperation()
        isSmallSpoonActive:=TRUE;           ! Set small spoon active flag
        pickSmallSpoon;                     ! Pick up small spoon
        
        retryCount := 0;                    ! Initialize retry counter
        ! Continue scooping until difference < 0.0015g or max retries reached
        WHILE averageWeightDifference >= 0.0015 AND retryCount < 50 DO
            previousWeightReading:=recvReading; ! Record current weight reading
            g_SetForce 100;                 ! Set gripper force to 100N
            calculateDifference;            ! Calculate weight difference
            shakeSmallSpoon;                ! Shake small spoon (parameters from Python)
            
            ! Dynamic wait time based on difference (1-3 seconds)
            WaitTime MAX(1, MIN(3, 1 + averageWeightDifference*2));
            
            currentWeightReading:=recvReading;  ! Record new weight reading
            loadNoDroppingThreshold;        ! Calculate no dropping threshold
            
            weightChange:=currentWeightReading-previousWeightReading; ! Calculate weight change
            TPWrite "weightChange small: " \Num:=weightChange; ! Display weight change
            
            ! Only scoop if weight change is below no dropping threshold
            IF weightChange < noDroppingThreshold THEN
                scoopSmall;                 ! Scoop material with small spoon
            ENDIF
            
            ! Dynamic wait time for stabilization
            WaitTime MAX(1, MIN(3, 1 + averageWeightDifference*2));
            calculateDifference;            ! Recalculate weight difference
            retryCount := retryCount + 1;  ! Increment retry counter
        ENDWHILE
        
        ! Handle max retry case
        IF retryCount >= 50 THEN
            overError := 2;                 ! Set timeout error
            isSend := TRUE;
        ENDIF
        
        returnSmallSpoon;                   ! Return small spoon to storage
        isSmallSpoonActive:=FALSE;          ! Clear small spoon active flag
    ENDPROC
    
    ! ==========================================================================
    ! Weight and Difference Calculation
    ! ==========================================================================
    
    ! Calculate average weight difference from 5 measurements
    PROC calculateDifference()
        WaitTime 0.5;                       ! Short delay for stabilization
        WaitUntil isRecvStable;             ! Wait until weight reading is stable
        
        ! Take 5 weight difference measurements
        weightDifference1:= targetWeight - recvReading + vialWeight;
        WaitUntil isRecvStable;
        weightDifference2:= targetWeight - recvReading + vialWeight;
        WaitUntil isRecvStable;
        weightDifference3:= targetWeight - recvReading + vialWeight;
        WaitUntil isRecvStable;
        weightDifference4:= targetWeight - recvReading + vialWeight;
        WaitUntil isRecvStable;
        weightDifference5:= targetWeight - recvReading + vialWeight;
        
        ! Calculate average difference
        averageWeightDifference:=(weightDifference1+weightDifference2+weightDifference3+weightDifference4+weightDifference5)/5;
        TPWrite "calculated difference: " \Num:=averageWeightDifference; ! Display result
    ENDPROC
    
    ! Load no dropping threshold based on spoon size
    PROC loadNoDroppingThreshold()
        ! Dynamic no dropping threshold based on active spoon
        IF isSmallSpoonActive=TRUE THEN
            noDroppingThreshold:=0.001;     ! Small spoon threshold: 0.001g
        ELSEIF isMediumSpoonActive=true THEN 
            noDroppingThreshold:=0.002;     ! Medium spoon threshold: 0.002g
        ELSE
            noDroppingThreshold:=0.1;       ! Large spoon threshold: 0.1g
        ENDIF
    ENDPROC
    
    ! ==========================================================================
    ! Preshaking Procedures
    ! ==========================================================================
    
    ! Preshaking for large spoon with bounded shake count
    PROC preshakeLargeSpoon()
        calculateDifference;                ! Calculate initial weight difference
        
        ! Calculate shake count with bounds (5-100 shakes)
        num shakeCount := MAX(5, MIN(100, (2-averageWeightDifference)*45));
        
        ! Perform preshaking movements
        FOR i FROM 1 TO shakeCount DO
            MoveAbsJ [[61.3649,-69.2156,50.7232,160.004,60.9019,5.67889],[-55.6397,9E+09,9E+09,9E+09,9E+09,9E+09]]\NoEOffs, vmax, z50, tool1;
            MoveAbsJ [[60.9589,-69.7126,49.9293,156.814,57.8666,7.65028],[-56.3405,9E+09,9E+09,9E+09,9E+09,9E+09]]\NoEOffs, v300, z50, tool1;
        ENDFOR
    ENDPROC
    
    ! ==========================================================================
    ! Error Detection and Handling
    ! ==========================================================================
    
    ! Funnel or spoon blocking detection
    PROC detectFunnelOrSpoonBlocking()
        VAR num i:=1;
        
        ! Check for 15 consecutive identical weight readings
        WHILE i < 15 DO 
            IF i < 15 THEN
                IF weightHistory{i} = weightHistory{i+1} THEN
                    i:=i+1;                 ! Increment counter if weights match
                    WaitTime 0.2;           ! Short delay between checks
                ELSE
                    i:=666;                 ! Reset counter if weights differ
                ENDIF
            ENDIF
        ENDWHILE 
        
        ! Handle blocking condition
        IF i=15 THEN
            ! Blocking detected - stop all operations
            isOperationEnabled:=FALSE;      ! Disable normal operation
            isBlocking:=TRUE;               ! Set blocking flag
            StopMove;                      ! Immediately stop robot movement
            TPWrite "BLOCKING DETECTED - STOPPING MOVEMENT";
        ENDIF
    ENDPROC
    
    ! Save current weight to history array
    PROC saveWeightToHistory()
        VAR num i:=0;
        ! Shift weight history and add new reading
        FOR i FROM 2 TO 15 DO
            weightHistory{i-1} := weightHistory{i};
        ENDFOR
        weightHistory{15} := recvReading;   ! Add new reading to end of array
    ENDPROC
    
    ! Determine if dispensing error occurred
    PROC determineDispensingError()
        turn_vial;                          ! Turn vial for error inspection
        
        ! Check if weight difference exceeds threshold (±0.02g)
        IF resultArray{2} > 0.02 OR resultArray{2} < -0.02 THEN 
            overError:=1;                   ! Set over error flag
        ENDIF
        isSend:=TRUE;                       ! Set send message flag
    ENDPROC
    
    ! ==========================================================================
    ! Result Processing
    ! ==========================================================================
    
    ! Get dispensing results
    PROC calculateDispensingResults()
        ! Implementation for calculating dispensing results
        ! This would include precision calculation, difference analysis, etc.
    ENDPROC
    
    ! ==========================================================================
    ! Spoon Handling Procedures (Placeholder Implementations)
    ! ==========================================================================
    
    PROC pickLargeSpoon()    ! Pick up large spoon from storage
    ENDPROC
    PROC shakeLargeSpoon()   ! Shake large spoon to remove excess material
    ENDPROC
    PROC scoopLarge()        ! Scoop material with large spoon
    ENDPROC
    PROC returnLargeSpoon()    ! Return large spoon to storage
    ENDPROC
    
    PROC pickMediumSpoon()   ! Pick up medium spoon from storage
    ENDPROC
    PROC shakeMediumSpoon()  ! Shake medium spoon to remove excess material
    ENDPROC
    PROC scoopMedium()       ! Scoop material with medium spoon
    ENDPROC
    PROC returnMediumSpoon()   ! Return medium spoon to storage (fixed typo)
    ENDPROC
    
    PROC pickSmallSpoon()    ! Pick up small spoon from storage
    ENDPROC
    PROC shakeSmallSpoon()   ! Shake small spoon to remove excess material
    ENDPROC
    PROC scoopSmall()        ! Scoop material with small spoon
    ENDPROC
    PROC returnSmallSpoon()    ! Return small spoon to storage
    ENDPROC
    
    ! ==========================================================================
    ! Miscellaneous Procedures
    ! ==========================================================================
    
    PROC openScaleDoor()          ! Open scale door
    ENDPROC
    PROC closeScaleDoor()         ! Close scale door
    ENDPROC
    PROC placeVialInScaleArea()       ! Place vial in scale
    ENDPROC
    PROC removeVialFromScale()      ! Remove vial from scale
    ENDPROC
    PROC returnVialToRack()          ! Return vial to rack
    ENDPROC
    PROC turnVial()          ! Turn vial
    ENDPROC
ENDMODULE