MODULE T_SOC_COM
    ! Module: T_SOC_COM MainModule
    ! Purpose: Handles socket communication between robot and external systems
    ! Collaborates with: T_ROB_L (left arm), T_ROB_R (right arm)
    ! Communications: Scale server (weight data), Command server (control commands)
    ! Protocol: TCP/IP socket communication
    
    ! Socket device for scale server
    VAR socketdev scaleServerSocket;
    ! Socket device for scale client connection
    VAR socketdev scaleClientSocket;
    ! Flag indicating scale client connection status
    VAR bool scaleClient_connected := FALSE;
    ! Socket device for command server
    VAR socketdev commandServerSocket;
    ! Socket device for command client connection
    VAR socketdev commandClientSocket;
    ! Flag indicating command client connection status
    VAR bool commandClient_connected := FALSE;
    ! Status of scale socket connection
    VAR socketstatus scaleSocketStat;
    ! Status of command socket connection
    VAR socketstatus commandSocketStat;
    ! IP address of connected client
    VAR string client_ip;
    ! Received message from scale socket
    VAR string scale_recv_msg;
    ! Received message from command socket
    VAR string command_recv_msg;
    ! Received weight reading from scale (kg)
    PERS num recv_reading;
    ! Received target weight from command socket (kg)
    PERS num recv_target_weight;
    ! Indicates if system is ready for new command
    PERS bool ready_new_command;
    ! Overall client connection status
    PERS bool client_connected := TRUE;
    ! Indicates if error and weight data are ready
    VAR bool ready; ! the error and now weight ready
    ! Difference between target and actual weight
    PERS num difference:=2.94725;
    ! Result array: [precision, difference, target_weight, sample_num, state_value]
    PERS num result{5};!first parameter is precision, 2nd is difference, 3nd is targetweight, 4nd sample num, 5nd default state value 
    ! Counter for total vials processed
    VAR num no_vials_now:=0;
    ! Flag to send results via socket
    PERS bool send_result;
    ! Indicates if weight readings are stable
    PERS bool recv_stable;
    ! Timer for socket operations
    VAR clock timer;
    ! Command array from fuzzy logic controller:
    ! command{1}: target weight (kg)
    ! command{2}: FLC output for shaking parameter
    ! command{3}: received weight (kg)
    ! command{4}: angle parameter for small spoon
    PERS num command{4}; 
    ! Shake parameter from FLC
    PERS num shake;
    ! Received JSON message from socket
    VAR string rec_json;! should 1 means connected 
    ! Connection received flag
    VAR bool con_rec;
    ! Indicates if vial weight is ready
    PERS bool weight_vial_reday;
    ! Average vial weight (kg)
    PERS num weight_vial;
    ! Angle parameter for small spoon from FLC
    PERS num a_smallspoon;


    
    
    ! Procedure: ServerStart
    ! Purpose: Initializes socket servers for scale and command communication
    ! Parameters: Recover - boolean flag indicating recovery mode
    ! Process: Creates, binds, and listens on sockets; accepts client connections
    ! Usage: Called at start of program and during recovery
    PROC ServerStart(bool Recover)
        IF Recover THEN
            TPWrite "ServerStart with recovery";
            SocketClose scaleServerSocket;
            SocketClose scaleClientSocket;
            SocketClose commandServerSocket;
            SocketClose commandClientSocket;
        ELSE
            TPWrite "ServerStart without recovery";
        ENDIF
        SocketCreate scaleServerSocket;
        SocketBind scaleServerSocket, "192.168.125.1", 1025;
        recv_reading := 0;
        TPWrite "scale socket binded";
        SocketCreate commandServerSocket;
        SocketBind commandServerSocket, "192.168.125.1", 1023;
        TPWrite "command socket binded";
        SocketListen scaleServerSocket;
        SocketListen commandServerSocket;
        scaleSocketStat := SocketGetStatus(scaleServerSocket);
        commandSocketStat := SocketGetStatus(commandServerSocket);
        IF (scaleSocketStat = SOCKET_LISTENING) AND (commandSocketStat = SOCKET_LISTENING)THEN
            TPWrite "listening for connection on scale server";
            SocketAccept scaleServerSocket, scaleClientSocket\ClientAddress:=client_ip, \Time:=30;
            scaleClient_connected := TRUE;
            TPWrite "scale client accepted for connection from "+ client_ip;
            
            TPWrite "listening for connection on command server";
            SocketAccept commandServerSocket, commandClientSocket\ClientAddress:=client_ip, \Time:=30;
            commandClient_connected := TRUE;
            TPWrite "command client accepted for connection from "+ client_ip;
            client_connected := scaleClient_connected AND commandClient_connected;
        ENDIF
        
        ERROR
            IF ERRNO=ERR_SOCK_TIMEOUT THEN
                TPWrite "Socket connection timed out while listenning";
                RETRY;
            ELSEIF ERRNO=ERR_SOCK_CLOSED THEN
                TPWrite "Can't start a server. Socket is  closed";
                RETURN;
            ELSE
                TPWrite "Unknown error";
                RETURN;
            ENDIF
    ENDPROC
    ! Procedure: Parsemsg
    ! Purpose: Parses incoming command messages from socket
    ! Parameters: msg - string message to parse
    ! Process: Extracts parameters from message, stores in command array
    ! Format: Parameters separated by spaces, ending with # character
    ! Usage: Called when command messages are received
    PROC Parsemsg(string msg)! this is to assign the receieved message to command which include the fuzzy controlling parameters

!//Local variables
        VAR bool auxOk;
        VAR num ind:=1;
        VAR num newInd;
        VAR num length;
        VAR num indParam:=1;
        VAR string subString;
        VAR bool end:=FALSE;
        VAR num nParams;

        !//Find the end character
        length:=StrMatch(msg,1,"#");
        IF length>StrLen(msg) THEN
            !//Corrupt message
            nParams:=-1;
   
        ELSE    
              
                !//
                WHILE end=FALSE DO
                    newInd:=StrMatch(msg,ind," ")+1;
                    IF newInd>length THEN
                        end:=TRUE;
                    ELSE
                        subString:=StrPart(msg,ind,newInd-ind-1);
                        auxOk:=StrToVal(subString,command{indParam});
                        indParam:=indParam+1;
                        ind:=newInd;
                    ENDIF
                ENDWHILE
                nParams:=indParam-1;
            
     ENDIF
    ENDPROC
    
    ! Procedure: main
    ! Purpose: Main communication loop for socket operations
    ! Process: Initializes variables, starts servers, handles incoming/outgoing messages
    ! Flow: Setup ? ServerStart ? Message handling loop ? Cleanup
    ! Message Handling: Scale data, command processing, result sending
    PROC main()

        weight_vial_reday:=false;
        con_rec:=FALSE;
        send_result:=False;!
        recv_stable:=FALSE;
        ready:=FALSE;
        client_connected := false;!
        ready_new_command := TRUE;
        ServerStart FALSE;
        WHILE client_connected = TRUE DO
            SocketReceive scaleClientSocket \Str := rec_json;
            
          IF send_result THEN ! send_result true means dispensing process end and the result is ready to be sent
              Socketsend scaleClientSocket \Str :=numToStr(result{1},5)+" " + numToStr(result{2},4)+" "+ ValToStr(result{3})+" "+numToStr(result{4},1);  
              !send_result:=FALSE;
              
              TPWrite "result"+ ValToStr(result{1})+" " + ValToStr(result{2})+" "+ ValToStr(result{3})+" "+ValToStr(result{4})+" "+ValToStr(result{5});
          ELSE 
              
            Socketsend scaleClientSocket \Str :="9 9 9";   ! send_result false only trigger sending 9 9 9 which the pyhthon not save the unready result
            
          ENDIF
          
          IF weight_vial_reday=TRUE THEN
              
          Socketsend commandClientSocket \Str := ValToStr(weight_vial);

          ENDIF 
          weight_vial_reday:=FALSE;
          
        
         IF ready_new_command = TRUE THEN!
                no_vials_now:= no_vials_now+1;
               
                Socketsend commandClientSocket \Str := "new_target";

                SocketReceive commandClientSocket \Str :=  command_recv_msg;
                Parsemsg(command_recv_msg);
                


                recv_target_weight:=command{1};
              
                ready_new_command := FALSE;
            ELSE
                Socketsend commandClientSocket \Str := "executing";
                SocketReceive commandClientSocket \Str :=  command_recv_msg;
                Parsemsg(command_recv_msg);

            ENDIF
            
                IF command{3}=100 or command{2}=1000 or command{4}=1000 THEN  ! the value can be changed just for noting the receieve data no stable
           
    
                 recv_stable:=false;
            
           ELSE
                      shake:=command{2};
                recv_reading:=command{3};
                a_smallspoon:=command{4};
                 recv_stable:=TRUE;
           ENDIF
                
        ENDWHILE
        client_connected := FALSE;
        SocketClose scaleServerSocket;
        SocketClose scaleClientSocket;
        TPWrite "program ended";
 
        ERROR
            IF ERRNO=ERR_SOCK_TIMEOUT THEN
                TPWrite "Timeout while waiting for message! restarting connection and retrying!!!";
                ! Close connection and restart.
                ServerStart TRUE;
                Retry;
            ELSEIF ERRNO=ERR_SOCK_CLOSED THEN
                TPWrite "Socket closed by client!, terminating";
                client_connected := FALSE;
                SocketClose scaleServerSocket;
                SocketClose scaleClientSocket;
                RETURN;
            ELSE
                TPWrite "Unknown error";
        ENDIF
        
	ENDPROC 
    
ENDMODULE