MODULE MainModule
    ! ==========================================================================
    ! T_SOC_COM - Communication Module for Yumi Robot
    ! Main function: Socket communication with external systems
    ! Features: Dual socket servers, message parsing, shared variable synchronization
    ! ==========================================================================

    ! ----------------------------
    ! Socket Configuration Constants
    ! ----------------------------
    CONST string SERVER_IP := "192.168.125.1"; ! Robot server IP address
    CONST num SCALE_SERVER_PORT := 1025;         ! Scale communication port
    CONST num COMMAND_SERVER_PORT := 1023;       ! Command communication port
    CONST num SOCKET_TIMEOUT := 60;              ! Socket timeout in seconds (increased from 30)
    CONST num MAX_RETRY_COUNT := 5;              ! Maximum connection retry count
    
    ! ----------------------------
    ! Security Configuration
    ! ----------------------------
    ! Client IP whitelist for secure connections
    PERS string allowed_ips{3} := ["192.168.125.2", "192.168.125.3", "192.168.125.4"];
    
    ! ----------------------------
    ! Socket Device Variables
    ! ----------------------------
    VAR socketdev scaleServerSocket;      ! Scale server socket
    VAR socketdev scaleClientSocket;      ! Scale client socket connection
    VAR socketdev commandServerSocket;    ! Command server socket
    VAR socketdev commandClientSocket;    ! Command client socket connection
    
    ! ----------------------------
    ! Socket Status Variables
    ! ----------------------------
    VAR socketstatus scaleSocketStatus;   ! Scale socket status
    VAR socketstatus commandSocketStatus; ! Command socket status
    VAR string clientIp;                  ! Connected client IP address
    
    ! ----------------------------
    ! Message Variables
    ! ----------------------------
    VAR string scaleRecvMsg;              ! Scale server received message
    VAR string commandRecvMsg;            ! Command server received message
    VAR string recvJsonMsg;               ! JSON received message
    
    ! ----------------------------
    ! Shared Variables (Persistent)
    ! ----------------------------
    PERS num recvReading;                 ! Received weight reading from scale
    PERS num recvTargetWeight;            ! Received target weight
    PERS bool isReadyNewCommand;          ! Ready for new command flag
    PERS bool isClientConnected := FALSE; ! Overall client connection status
    PERS num weightDifference:=2.94725;   ! Weight difference
    ! Result array: [precision, difference, target_weight, sample_num, default_state]
    PERS num resultArray{5};               
    PERS bool isRecvStable;               ! Weight reading stable flag
    PERS num commandArray{4};             ! Command array: [target_weight, fuzzy_shake, rec_weigh, angle]
    PERS num shakeParameter;              ! Shake parameter from fuzzy controller
    PERS bool isSendResult;               ! Send result flag
    PERS num vialWeight;                  ! Vial weight
    PERS num smallSpoonParameter;         ! Small spoon parameter
    
    ! ----------------------------
    ! Module-Specific Variables
    ! ----------------------------
    VAR bool isErrorAndWeightReady;       ! Error and weight ready flag
    VAR num currentVialCount:=0;          ! Current number of vials dispensed
    VAR clock operationTimer;             ! Operation timer
    VAR bool isConnectionReceived;        ! Connection received flag
    VAR bool isVialWeightReady:=FALSE;    ! Vial weight ready flag
    VAR num retryCount := 0;              ! Retry counter for connections
    
    ! ==========================================================================
    ! Server Start Procedure with Recovery
    ! ==========================================================================
    PROC ServerStart(bool Recover)
        ! Display server start status
        IF Recover THEN
            TPWrite "ServerStart with recovery - Attempt " + ValToStr(retryCount + 1);
        ELSE
            TPWrite "ServerStart without recovery";
            retryCount := 0;                ! Reset retry counter for fresh start
        ENDIF
        
        ! Always close sockets before creating new ones to avoid "socket already created" error
        SocketClose scaleServerSocket;
        SocketClose scaleClientSocket;
        SocketClose commandServerSocket;
        SocketClose commandClientSocket;
        
        ! Initialize connection status
        isClientConnected := FALSE;
        
        ! ----------------------------
        ! Create and Bind Scale Socket
        ! ----------------------------
        SocketCreate scaleServerSocket;
        SocketBind scaleServerSocket, SERVER_IP, SCALE_SERVER_PORT;
        TPWrite "Scale socket bound to " + SERVER_IP + ":" + ValToStr(SCALE_SERVER_PORT);
        
        ! ----------------------------
        ! Create and Bind Command Socket
        ! ----------------------------
        SocketCreate commandServerSocket;
        SocketBind commandServerSocket, SERVER_IP, COMMAND_SERVER_PORT;
        TPWrite "Command socket bound to " + SERVER_IP + ":" + ValToStr(COMMAND_SERVER_PORT);
        
        ! ----------------------------
        ! Start Listening on Both Sockets
        ! ----------------------------
        SocketListen scaleServerSocket;
        SocketListen commandServerSocket;
        
        ! Get initial socket status
        scaleSocketStatus := SocketGetStatus(scaleServerSocket);
        commandSocketStatus := SocketGetStatus(commandServerSocket);
        
        ! ----------------------------
        ! Accept Client Connections
        ! ----------------------------
        IF (scaleSocketStatus = SOCKET_LISTENING) AND (commandSocketStatus = SOCKET_LISTENING)THEN
            TPWrite "Listening for connections...";
            
            ! Accept scale client connection with timeout
            SocketAccept scaleServerSocket, scaleClientSocket\ClientAddress:=clientIp, \Time:=SOCKET_TIMEOUT;
            TPWrite "Scale client accepted from " + clientIp;
                
            ! Accept command client connection with timeout
            SocketAccept commandServerSocket, commandClientSocket\ClientAddress:=clientIp, \Time:=SOCKET_TIMEOUT;
            TPWrite "Command client accepted from " + clientIp;
            TPWrite "Both sockets connected successfully!";
            isClientConnected := TRUE;
        ELSE
            TPWrite "Failed to start listening on sockets!";
            CloseAllSockets;
        ENDIF
        
        ! ----------------------------
        ! Error Handling for ServerStart
        ! ----------------------------
        ERROR
            IF ERRNO=ERR_SOCK_TIMEOUT THEN
                TPWrite "Socket connection timed out while listening";
                
                ! Retry connection if under max retry count
                IF retryCount < MAX_RETRY_COUNT THEN
                    retryCount := retryCount + 1;
                    WaitTime 2; ! Short delay before retry
                    RETRY;
                ELSE
                    TPWrite "Max retry count reached. Exiting.";
                    CloseAllSockets;
                    RETURN;
                ENDIF
            ELSEIF ERRNO=ERR_SOCK_CLOSED THEN
                TPWrite "Cannot start server. Socket is closed";
                CloseAllSockets;
                RETURN;
            ELSE
                TPWrite "Unknown server start error: " + NumToStr(ERRNO, 0);
                CloseAllSockets;
                RETURN;
            ENDIF
    ENDPROC
    
    ! ==========================================================================
    ! Main Communication Loop
    ! ==========================================================================
    PROC main()
        ! ----------------------------
        ! Initialization
        ! ----------------------------
        InitializeVariables; ! Reset all communication variables
        
        ! Start server connections
        ServerStart(FALSE);
        
        ! ----------------------------
        ! Main Communication Loop
        ! ----------------------------
        WHILE isClientConnected = TRUE DO
            SocketReceive scaleClientSocket \Str := recvJsonMsg;
            
            ! Validate received message length
            IF StrLen(recvJsonMsg) > 0 THEN
                ! Process scale message (if needed)
                TPWrite "Scale message received: " + recvJsonMsg;
            ENDIF
            
            ! ----------------------------
            ! Send Results or Placeholder
            ! ----------------------------
            IF isSendResult THEN 
                ! Send dispensing results when ready
                SendDispensingResults;
            ELSE
                ! Send placeholder when results not ready
                SocketSend scaleClientSocket \Str := "9 9 9";
            ENDIF
            
            ! ----------------------------
            ! Handle Vial Weight Data
            ! ----------------------------
            IF isVialWeightReady THEN
                ! Send vial weight to command client
                SocketSend commandClientSocket \Str := ValToStr(vialWeight);
                isVialWeightReady := FALSE; ! Reset flag after sending
            ENDIF 
            
            ! ----------------------------
            ! Handle Command Server Communication
            ! ----------------------------
            IF isReadyNewCommand THEN
                ! Request new target weight
                RequestNewTargetWeight;
            ELSE
                ! Report executing status and receive command updates
                UpdateExecutionStatus;
            ENDIF
            
            ! ----------------------------
            ! Update Shared Variables
            ! ----------------------------
            UpdateSharedVariables;
        ENDWHILE
        
        ERROR
            ! Handle communication errors
            IF ERRNO=ERR_SOCK_TIMEOUT THEN
                TPWrite "Timeout while waiting for message! Restarting connection...";
                ! Close and restart connections
                ServerStart(TRUE);
                Retry; ! Retry the communication loop
            ELSEIF ERRNO=ERR_SOCK_CLOSED THEN
                TPWrite "Socket closed by client! Terminating...";
                isClientConnected := FALSE;
                CloseAllSockets;
            ELSE
                TPWrite "Unknown communication error: " + NumToStr(ERRNO, 0);
                ! Attempt to recover by restarting connections
                ServerStart(TRUE);
                Retry;
            ENDIF
            ! ----------------------------
            ! Cleanup and Exit
            ! ----------------------------
            TPWrite "Communication loop exited. Closing connections...";
            CloseAllSockets;
            isClientConnected := FALSE;
            TPWrite "Program ended";
    ENDPROC
    
    ! ==========================================================================
    ! Message Parsing Procedure
    ! ==========================================================================
    PROC ParseMessage(string msg)
        ! Local variables for message parsing
        VAR bool auxOk;
        VAR num ind:=1;
        VAR num newInd;
        VAR num length;
        VAR num indParam:=1;
        VAR string subString;
        VAR bool end:=FALSE;
        VAR num nParams;
        
        ! Find the end character '#'
        length := StrMatch(msg, 1, "#");
        
        IF length > StrLen(msg) THEN
            ! Corrupt message - no end character found
            nParams := -1;
            TPWrite "Corrupt message received: " + msg;
        ELSE    
            ! Parse message parameters separated by spaces
            WHILE NOT end DO
                newInd := StrMatch(msg, ind, " ") + 1;
                
                IF newInd > length THEN
                    end := TRUE;
                ELSE
                    ! Extract parameter substring
                    subString := StrPart(msg, ind, newInd - ind - 1);
                    
                    ! Convert string to numeric value and store in command array
                    IF indParam <= Dim(commandArray, 1) THEN
                        auxOk := StrToVal(subString, commandArray{indParam});
                        IF NOT auxOk THEN
                            TPWrite "Failed to parse parameter " + ValToStr(indParam) + ": " + subString;
                        ENDIF
                        indParam := indParam + 1;
                    ENDIF
                    
                    ind := newInd;
                ENDIF
            ENDWHILE
            
            nParams := indParam - 1;
            TPWrite "Parsed " + ValToStr(nParams) + " parameters from message";
        ENDIF
    ENDPROC
    
    ! ==========================================================================
    ! Helper Procedures
    ! ==========================================================================
    
    ! Initialize all communication variables
    PROC InitializeVariables()
        ! Reset connection and status flags
        isVialWeightReady := FALSE;
        isConnectionReceived := FALSE;
        isSendResult := FALSE;
        isRecvStable := FALSE;
        isErrorAndWeightReady := FALSE;
        isClientConnected := FALSE;
        isReadyNewCommand := TRUE;
        
        ! Reset numeric variables
        recvReading := 0;
        weightDifference := 2.94725;
        currentVialCount := 0;
        
        ! Reset arrays
        FOR i FROM 1 TO Dim(resultArray, 1) DO
            resultArray{i} := 0;
        ENDFOR
        
        FOR i FROM 1 TO Dim(commandArray, 1) DO
            commandArray{i} := 0;
        ENDFOR
        
        TPWrite "All variables initialized";
    ENDPROC
    
    ! Close all socket connections
    PROC CloseAllSockets()
        SocketClose scaleServerSocket;
        SocketClose scaleClientSocket;
        SocketClose commandServerSocket;
        SocketClose commandClientSocket;
        TPWrite "All sockets closed";
    ENDPROC
    
    ! Send dispensing results to scale client
    PROC SendDispensingResults()
        ! Format and send results
        SocketSend scaleClientSocket \Str := 
            NumToStr(resultArray{1}, 5) + " " + 
            NumToStr(resultArray{2}, 4) + " " + 
            ValToStr(resultArray{3}) + " " + 
            NumToStr(resultArray{4}, 1);  
        
        ! Display results on teach pendant
        TPWrite "Sent result: " + 
            ValToStr(resultArray{1}) + " " + 
            ValToStr(resultArray{2}) + " " + 
            ValToStr(resultArray{3}) + " " + 
            ValToStr(resultArray{4}) + " " + 
            ValToStr(resultArray{5});
        
        ! Reset send result flag after sending
        isSendResult := FALSE;
    ENDPROC
    
    ! Request new target weight from command client
    PROC RequestNewTargetWeight()
        ! Increment vial count
        currentVialCount := currentVialCount + 1;
        
        ! Send new target request
        SocketSend commandClientSocket \Str := "new_target";
        
        ! Receive and parse command response
        SocketReceive commandClientSocket \Str := commandRecvMsg;
        ParseMessage(commandRecvMsg);
        
        ! Update target weight from parsed command
        recvTargetWeight := commandArray{1};
        
        ! Mark as executing
        isReadyNewCommand := FALSE;
        
        TPWrite "New target weight received: " + ValToStr(recvTargetWeight);
    ENDPROC
    
    ! Update execution status and receive command updates
    PROC UpdateExecutionStatus()
        ! Send executing status
        SocketSend commandClientSocket \Str := "executing";
        
        ! Receive and parse command updates
        SocketReceive commandClientSocket \Str := commandRecvMsg;
        ParseMessage(commandRecvMsg);
    ENDPROC
    
    ! Update shared variables based on parsed command
    PROC UpdateSharedVariables()
        ! Enhanced data stability detection
        IF IsDataStable() THEN
            ! Update shared variables with stable data
            shakeParameter := commandArray{2};
            recvReading := commandArray{3};
            smallSpoonParameter := commandArray{4};
            isRecvStable := TRUE;
        ELSE
            ! Mark data as unstable
            isRecvStable := FALSE;
        ENDIF
    ENDPROC
    
    ! Check if received data is stable
    FUNC bool IsDataStable()
        ! Enhanced stability check with multiple conditions
        ! Check for invalid extreme values
        IF commandArray{3} = 100 OR commandArray{2} = 1000 OR commandArray{4} = 1000 THEN
            RETURN FALSE;
        ENDIF
        
        ! Check for reasonable weight range (adjust based on application needs)
        IF recvTargetWeight > 0 AND (commandArray{3} < 0 OR commandArray{3} > recvTargetWeight * 2) THEN
            RETURN FALSE;
        ENDIF
        
        RETURN TRUE;
    ENDFUNC
ENDMODULE