MODULE MainModule
    ! ==========================================================================
    ! T_ROB_L - Left Arm Module for Yumi Robot
    ! Main function: Sample vial handling, hopper operations, and collaboration
    ! Features: Vial pickup/placement, hopper handling, result processing
    ! ==========================================================================

    ! ----------------------------
    ! Tool and Work Object Data
    ! ----------------------------
    ! Tool configuration for left arm gripper
    TASK PERS tooldata tool1:=[TRUE,[[0,0,0],[1,0,0,0]],[-1,[0,0,0],[1,0,0,0],0,0,0]];
    
    ! Calibrated workpiece coordinate system for robot positioning
    TASK PERS wobjdata wobjCalib:=[FALSE,TRUE,"",[[314.034,274.803,1.24622],[0.999945,-0.00160565,-0.00835892,0.00614249]],[[0,0,0],[1,0,0,0]]];

    ! ----------------------------
    ! Target Positions - Sample Vial Rack
    ! ----------------------------
    ! Sample vial pickup positions (low height)
    CONST robtarget p1:=[[330.40,187.06,55.05],[0.0139775,-0.020723,-0.999489,-0.0199153],[-1,2,0,4],[134.391,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! Low position 1
    CONST robtarget p2:= [[329.89,160.36,55.67],[0.0139952,-0.0207114,-0.999489,-0.0199133],[-1,2,0,4],[134.388,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! Low position 2
    CONST robtarget p3:=[[329.26,133.87,55.35],[0.0139876,-0.0207179,-0.999489,-0.0199247],[-1,2,0,4],[134.387,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! Low position 3
    
    ! Sample vial placement positions (high height)
    CONST robtarget p4:=[[330.40,187.06,69.2],[0.0139775,-0.020723,-0.999489,-0.0199153],[-1,2,0,4],[134.391,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! High position 1
    CONST robtarget p5:= [[329.89,160.36,69.82],[0.0139952,-0.0207114,-0.999489,-0.0199133],[-1,2,0,4],[134.388,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! High position 2
    CONST robtarget p6:=[[329.26,133.87,69.5],[0.0139876,-0.0207179,-0.999489,-0.0199247],[-1,2,0,4],[134.387,9E+09,9E+09,9E+09,9E+09,9E+09]]; ! High position 3

    ! ----------------------------
    ! Additional Target Positions
    ! ----------------------------
    CONST robtarget p10:=[[299.68,80.02,169.52],[0.0102995,0.99639,0.0801251,-0.026109],[-1,2,1,4],[-143.56,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p20:=[[453.12,102.65,225.77],[0.00579748,-0.998714,-0.0411077,0.0291069],[-1,1,1,4],[-157.101,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p30:=[[299.68,80.02,169.52],[0.0102997,0.996389,0.0801273,-0.0261071],[-1,2,1,4],[-143.56,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p40:=[[427.22,129.12,230.57],[0.091859,-0.956102,-0.277205,-0.024272],[-1,1,1,4],[-156.838,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p50:=[[439.43,114.31,264.04],[0.699911,0.711476,0.05739,0.0251471],[-1,1,1,5],[-153.491,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p60:=[[325.38,208.60,188.09],[0.678067,0.733916,-0.0378468,0.0126185],[-1,2,1,5],[-138.756,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p70:=[[378.97,240.59,222.67],[0.0411028,0.976728,0.168636,0.125996],[-1,2,1,4],[-148.764,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p1001:=[[301.89,156.60,180.11],[0.183512,-0.963973,-0.16544,0.098535],[-1,1,1,4],[-149.036,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p1011:=[[211.50,79.30,231.13],[0.0252822,-0.827633,0.557691,0.058009],[-1,-2,-2,4],[-164.438,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p110:=[[247.08,160.32,151.64],[3.51796E-05,0.724276,0.68951,-1.28981E-06],[-1,2,0,4],[-149.09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p120:=[[247.08,160.32,151.64],[3.40822E-05,0.724276,0.68951,-1.34519E-06],[-1,2,0,4],[-149.09,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p130:=[[362.05,158.18,147.11],[2.80182E-05,0.722942,0.690908,2.91471E-05],[-1,1,0,4],[-153.209,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p140:=[[305.77,157.09,220.88],[3.6465E-05,-0.715291,-0.698827,3.01124E-05],[-1,2,0,4],[-155.299,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p150:=[[243.76,154.69,193.15],[1.09473E-05,0.710452,0.703746,1.63528E-05],[-1,2,0,4],[-152.965,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST robtarget p160:=[[319.28,155.66,194.72],[0.0167441,0.727114,0.684933,0.0435041],[-1,2,0,4],[-155,9E+09,9E+09,9E+09,9E+09,9E+09]];

    ! ----------------------------
    ! Joint Target Positions
    ! ----------------------------
    CONST jointtarget jpost11:=[[-55.4377,-42.2272,62.2279,139.242,57.1562,82.6226],[87.2323,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos10:=[[-68.5043,-44.1919,60.936,146.266,67.9112,77.1878],[92.6016,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos20:=[[-71.9577,-58.9043,32.1212,-152.298,137.813,-211.546],[150.771,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos30:=[[-78.1389,-50.4919,45.2566,180.857,56.7489,-30.1953],[132.59,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos40:=[[-78.1389,-50.492,45.2564,180.857,56.7489,-30.1953],[132.59,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos50:=[[-77.0486,-42.0877,27.9661,131.239,39.9449,7.46354],[107.419,9E+09,9E+09,9E+09,9E+09,9E+09]];
    CONST jointtarget jpos60:=[[-63.4379,-46.221,35.0139,107.699,61.2269,27.8762],[69.6425,9E+09,9E+09,9E+09,9E+09,9E+09]];

    ! ----------------------------
    ! Speed and Zone Settings
    ! ----------------------------
    CONST speeddata v_move := v500;       ! General movement speed (500mm/s)
    CONST zonedata z_move := z10;         ! General zone size (10mm)
    
    ! ----------------------------
    ! Persistent Variables (Shared)
    ! ----------------------------
    PERS num recvReading:=9.735;           ! Received weight reading from scale
    PERS bool isClientConnected;            ! Client connection status
    PERS num recvTargetWeight;              ! Received target weight
    PERS bool isLeftFinish;                 ! Left arm completion flag
    PERS bool isReadyNewCommand;            ! Ready for new command flag
    PERS bool isVialPut;                    ! Vial placed flag
    PERS bool isVialBack;                   ! Vial returned flag
    PERS bool isDataLoadDone;               ! Data loading completion flag
    PERS num resultArray{5};                ! Result array
    PERS bool isSendResult;                 ! Send result flag
    PERS bool isInitialVialPut;             ! Initial vial placement flag
    PERS String targetWeightString;         ! Target weight string
    PERS bool isHopperPickDone;             ! Hopper pick completion flag
    PERS bool isHopperBack;                 ! Hopper back position flag
    PERS bool isHopperBackStart;            ! Hopper back start flag
    PERS num overError;                     ! Over error flag
    PERS bool isSend;                       ! Send message flag
    
    ! ----------------------------
    ! Temporary Variables
    ! ----------------------------
    VAR num targetWeight:=0;                ! Current target weight
    VAR num weightDifference;               ! Weight difference
    VAR num vialRackGapFlag;                ! Flag for calculating vial rack gaps
    VAR num currentVialCount:=0;            ! Current number of vials dispensed
    VAR num vialPositionIndex;              ! Remainder of vial count modulo 16
    VAR clock operationTimer;               ! Clock for timing operations
    VAR num operationTime;                  ! Total operation time in seconds

    ! ==========================================================================
    ! Main Program Entry
    ! ==========================================================================
    PROC main()
        ! Pre-dispensing initialization
        initializeLeftStart;                ! Initialize left arm system
        
        ! Vial handling phase
        placeVialInScaleArea;               ! Place vial in temporary holder
        WaitUntil isInitialVialPut;         ! Wait for initial vial placement
        
        ! Start timing the dispensing process
        ClkStart operationTimer;
        
        ! Signal hopper pick completion to right arm
        isHopperPickDone:=TRUE;
        
        ! Wait for hopper back signal from right arm
        WaitUntil isHopperBackStart;        ! Wait for right arm to finish dispensing
        returnHopperToStorage;              ! Return hopper to storage
        isHopperBack:=TRUE;                 ! Set hopper back flag
        
        ! Wait for send signal from error handling
        WaitUntil isSend;                   ! Wait for error determination to complete
        sendResultsToSocket;                ! Send results to external system
        
        ! Return vial to rack
        returnVialToRack;                   ! Return vial to sample rack
        isLeftFinish:=TRUE;                 ! Signal left arm completion
        
        ! Handle over error condition
        IF overError=1 THEN
            vialPositionIndex:=vialPositionIndex-1;  ! Adjust vial count for retry
        ENDIF    
    ENDPROC

    ! ==========================================================================
    ! Home and Calibration Positions
    ! ==========================================================================
    
    ! Move left arm to home position
    PROC leftHomePosition()
        MoveAbsJ [[0,-130,30,0,40,0],[135,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v6000, z50, GripperLeft;
    ENDPROC
    
    ! Move left arm to camera calibration position
    PROC leftCameraCalibration()
        MoveJ [[439.09,273.63,286.84],[0.50907,-0.490757,0.50908,-0.490758],[-1,0,0,5],[115.735,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
    ENDPROC

    ! ==========================================================================
    ! Initialization Procedures
    ! ==========================================================================
    
    ! Left arm initialization
    PROC initializeLeftStart()
        PERS bool isInitialLDone:=FALSE;     ! Left initialization completion flag
        
        g_GripIn;                           ! Close gripper initially
        
        ! Wait for system readiness
        WaitUntil isClientConnected;        ! Wait for socket connection
        WaitUntil isDataLoadDone;           ! Wait for data loading
        
        ! Reset flags and timers
        isLeftFinish:=FALSE;                ! Clear left arm finish flag
        ClkReset operationTimer;            ! Reset operation timer
        ClkStart operationTimer;            ! Start initialization timer
        
        isInitialLDone:=TRUE;               ! Set initialization done flag
    ENDPROC
    
    ! ==========================================================================
    ! Vial Handling Procedures
    ! ==========================================================================
    
    ! Handle vial placement in scale area
    PROC placeVialInScaleArea()
        ! Wait for client connection
        WaitUntil isClientConnected;        ! Ensure socket connection is active
        
        ! Update vial count and position
        currentVialCount:=currentVialCount+1;       ! Increment vial count
        vialPositionIndex:= (currentVialCount MOD 16)-1;  ! Calculate vial position index (0-15)
        
        ! Move to home position and pick vial
        leftHomePosition;                   ! Move to safe home position
        pickVialFromRack();                 ! Pick vial from rack
        leftHomePosition;                   ! Return to home position
    ENDPROC
    
    ! Pick vial from rack
    PROC pickVialFromRack()
        ! Move to vial rack area
        MoveAbsJ [[-10.6673,-112.178,45.0398,-30.5344,62.1438,120.456],[134.528,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
        MoveAbsJ [[-65.6477,-111.844,64.9464,134.812,109.778,-33.7355],[54.1405,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
        MoveL [[330.39,187.06,121.29],[0.0139927,-0.0207169,-0.999489,-0.0199197],[-1,2,0,4],[134.391,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        g_MoveTo 19;                        ! Move gripper to position 19
        
        ! Calculate vial position based on vialPositionIndex
        ! This logic determines which rack position to use based on vial index
        IF vialPositionIndex >= 0 AND vialPositionIndex <=5 THEN
            ! Use p1 as base position (positions 0-5)
            MoveL offs (p1, 35.25*vialPositionIndex, -1.442*vialPositionIndex, 0.09*vialPositionIndex), v200, z50, GripperLeft;
        ELSEIF vialPositionIndex >=6 AND vialPositionIndex <=9 THEN
            ! Use p2 as base position (positions 6-9)
            vialRackGapFlag := vialPositionIndex - 6;
            MoveL offs(p2, 35.088*vialRackGapFlag, -1.04*vialRackGapFlag, 0.304*vialRackGapFlag), v200, z50, GripperLeft;
        ELSE 
            ! Use p3 as base position (positions 10-15)
            vialRackGapFlag := vialPositionIndex - 10;
            MoveL offs(p3, 35.032*vialRackGapFlag, -0.87*vialRackGapFlag, -0.062*vialRackGapFlag), v200, z50, GripperLeft;
        ENDIF
        
        ! Perform vial pickup operation (simplified placeholder)
        g_GripOut;                          ! Open gripper to pick vial
        WaitTime 0.5;                       ! Wait for gripper movement
        g_SetForce 50;                      ! Set gripper force for vial pickup
        WaitTime 0.5;                       ! Wait for force application
        
        ! Lift vial and move to temporary holder
        MoveL [[330.39,187.06,121.29],[0.0139927,-0.0207169,-0.999489,-0.0199197],[-1,2,0,4],[134.391,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        
        ! Place vial in temporary holder
        ! (Detailed placement logic would go here)
        
        isVialPut:=TRUE;                    ! Set vial placed flag
    ENDPROC
    
    ! Return vial to rack
    PROC returnVialToRack()
        ! Implementation for returning vial to rack
        returnVialToRackPosition();         ! Return vial to rack position
    ENDPROC
    
    ! Return vial from temporary hole to rack
    PROC returnVialToRackPosition()
        ! Move to temporary holder position
        MoveAbsJ [[-37.3371,-118.785,57.7839,129.52,84.5365,-10.7997],[61.7534,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
        g_MoveTo 17.5;                      ! Move gripper to position 17.5
        
        ! Approach temporary holder
        MoveL [[370.33,-8.22,193.61],[0.0178566,-0.0241315,-0.999355,-0.0196915],[-1,1,-1,4],[135.434,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        
        ! Lower to temporary holder and grip vial
        MoveL [[370.34,-8.22,66.15],[0.017824,-0.0241463,-0.999356,-0.0196751],[-1,2,-1,4],[135.435,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        WaitTime 1.0;                       ! Wait for stabilization
        g_GripOut;                          ! Open gripper to release vial
        WaitTime 0.5;                       ! Wait for gripper movement
        
        ! Lift and move to rack position
        MoveL [[370.33,-8.22,193.61],[0.0178573,-0.0241336,-0.999355,-0.0196919],[-1,1,-1,4],[135.434,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        
        ! Place vial in correct rack position
        loop_backvial_pos();                ! Place vial in calculated rack position
        
        ! Return to safe position
        MoveL [[238.36,248.58,130.85],[0.0174666,-0.0393068,-0.998892,-0.0190914],[0,1,0,4],[142.817,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
    ENDPROC
    
    ! Loop through vial positions for return
    PROC returnVialToCalculatedPosition()
        ! Implementation for placing vial in correct rack position
        ! This would include logic similar to pick_vial_ready but for placement
        ! Using high positions (p4-p6) instead of low positions (p1-p3)
        
        ! Calculate position based on vialPositionIndex
        IF vialPositionIndex >= 0 AND vialPositionIndex <=5 THEN
            ! Use p4 as base position (high) for positions 0-5
            MoveL offs (p4, 35.25*vialPositionIndex, -1.442*vialPositionIndex, 0.09*vialPositionIndex), v200, z50, GripperLeft;
        ELSEIF vialPositionIndex >=6 AND vialPositionIndex <=9 THEN
            ! Use p5 as base position (high) for positions 6-9
            vialRackGapFlag := vialPositionIndex - 6;
            MoveL offs(p5, 35.088*vialRackGapFlag, -1.04*vialRackGapFlag, 0.304*vialRackGapFlag), v200, z50, GripperLeft;
        ELSE 
            ! Use p6 as base position (high) for positions 10-15
            vialRackGapFlag := vialPositionIndex - 10;
            MoveL offs(p6, 35.032*vialRackGapFlag, -0.87*vialRackGapFlag, -0.062*vialRackGapFlag), v200, z50, GripperLeft;
        ENDIF
        
        ! Place vial and release
        g_GripIn;                           ! Close gripper to release vial
        WaitTime 0.5;                       ! Wait for gripper movement
    ENDPROC
    
    ! ==========================================================================
    ! Hopper Handling Procedures
    ! ==========================================================================
    
    ! Return hopper to storage
    PROC returnHopperToStorage()
        ! Implementation for returning hopper to storage
        returnHopperSupportToStorage();     ! Execute hopper return sequence
    ENDPROC
    
    ! Return hopper support to storage box
    PROC returnHopperSupportToStorage()
        ! Move to hopper area
        MoveAbsJ [[-33.8484,-128.631,66.5416,261.555,21.0481,-192.885],[93.338,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
        
        ! Perform hopper return operations
        g_GripIn;                           ! Close gripper
        WaitTime 0.5;                       ! Wait for gripper movement
        
        ! Move hopper to storage position
        ! (Detailed storage placement logic would go here)
        
        ! Final movements to secure hopper in storage
        MoveL [[456.84,494.06,383.15],[0.519898,-0.467825,0.486736,-0.523387],[-1,0,0,4],[128.564,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        MoveL [[453.41,236.11,385.64],[0.491549,-0.497532,0.516603,-0.493926],[-1,2,-1,4],[128.86,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        
        ! Return to safe position
        MoveAbsJ [[-33.8484,-128.631,66.5416,261.555,21.0481,-192.885],[93.338,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
    ENDPROC
    
    ! Pick hopper and support structure
    PROC pickHopperAndSupport()
        ! Move to hopper pickup area
        MoveAbsJ [[-15.608,-130.004,50.1868,-20.3301,30.4243,80.9518],[96.198,9E+09,9E+09,9E+09,9E+09,9E+09]]NoEOffs, v1000, z50, GripperLeft;
        
        ! Approach and pick hopper
        MoveL [[291.55,510.24,346.57],[0.486579,-0.486492,0.535635,-0.489553],[0,0,0,4],[107.456,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        g_GripIn;                           ! Close gripper to pick hopper
        WaitTime 0.5;                       ! Wait for gripper movement
        
        ! Lift hopper and move to working position
        MoveL [[396.70,497.04,384.06],[0.47915,-0.494542,0.528272,-0.496761],[-1,1,0,4],[107.446,9E+09,9E+09,9E+09,9E+09,9E+09]], v1000, z50, GripperLeft;
        
        ! Additional movements to position hopper correctly
        ! (Detailed positioning logic would go here)
    ENDPROC
    
    ! ==========================================================================
    ! Result Processing and Communication
    ! ==========================================================================
    
    ! Send results to socket
    PROC sendResultsToSocket()
        ! Stop timer and calculate operation time
        ClkStop operationTimer;
        operationTime:=ClkRead(operationTimer);     ! Get total operation time in seconds
        
        ! Display operation time on teach pendant
        TPWrite "Operation time: " + ValToStr(operationTime) + " seconds";
        
        ! Update result array
        resultArray{4}:=operationTime;      ! Store operation time in result array
        
        ! Calculate performance score
        resultArray{5}:=-(100*0.7*abs(resultArray{1})+0.2*((operationTime/60)-10));
        
        ! Set send result flag based on error state
        IF overError=1 THEN
             isSendResult:=false;            ! Don't send result if over error
        ELSE
            isSendResult:=TRUE;               ! Send result if no error
        ENDIF
        
        ! Wait for stabilization and return to home
        WaitTime 1.0;                       ! Short delay for system stabilization
        LhomePos;                           ! Return to safe home position
        
        ! Reset flags and timer
        isSendResult:=FALSE;                ! Clear send result flag
        ClkReset operationTimer;            ! Reset operation timer
    ENDPROC
    
    ! ==========================================================================
    ! Test and Debug Procedures
    ! ==========================================================================
    
    ! Test procedure for vial handling
    PROC testVialHandling()
        ! Test movements for vial handling
        MoveJ p140, v1000, z50, tool1;
        g_Init;                             ! Initialize gripper
        MoveJ p110, v1000, z50, tool1;
        g_GripIn;                           ! Close gripper
        MoveJ p150, v1000, z50, tool1;
        MoveJ p160, v1000, z50, tool1;
        MoveJ p130, v1000, z50, tool1;
        g_GripOut;                          ! Open gripper
    ENDPROC
    
    ! Dynamic movement test procedure
    PROC testDynamicMovement()
        ! Test dynamic movement sequence
        MoveJ dyp01, v1000, z50, tool1;
        MoveJ dyp03, v1000, z50, tool1;
        MoveJ dyp02, v1000, z50, tool1;
    ENDPROC
ENDMODULE