// Arquero_Test.cpp: define el punto de entrada de la aplicación de consola.
//

#include "stdafx.h"

//Required include files
#include <stdio.h>	
#include <string>
#include <iostream>
#include "pubSysCls.h"	

using namespace sFnd;

// Send message and wait for newline
void msgUser(const char *msg) {
	std::cout << msg;
	getchar();
}

//*********************************************************************************
//This program will load configuration files onto each node connected to the port, then executes
//sequential repeated moves on each axis.
//*********************************************************************************

#define MAX_DISTANCE		35000 //Maxima distancia 35500 de sistema lineal!!!!!
#define MOVE_DISTANCE		12000 //Maxima distancia 12350 del arquero!!!!!
#define ROT_DISTANCE		1600 // Rotacion del arquero (Libre)
#define ACC_LIM_RPM_PER_SEC	10000
#define VEL_LIM_RPM			1200
#define MOVE_DISTANCE_CNTS	10000	
#define NUM_MOVES			5
#define CHANGE_NUMBER_SPACE	0	//The change to the numberspace after homing (cnts)
#define TIME_TILL_TIMEOUT	10000	//The timeout used for homing(ms)


int main(int argc, char* argv[])
{
	msgUser("Prueba de Arquero en proceso. Presione enter para continuar.");

	size_t portCount = 0;
	std::vector<std::string> comHubPorts;

	//Create the SysManager object. This object will coordinate actions among various ports
	// and within nodes. In this example we use this object to setup and open our port.
	SysManager* myMgr = SysManager::Instance();							//Create System Manager myMgr

																		//This will try to open the port. If there is an error/exception during the port opening,
																		//the code will jump to the catch loop where detailed information regarding the error will be displayed;
																		//otherwise the catch loop is skipped over
	try
	{

		SysManager::FindComHubPorts(comHubPorts);
		printf("Se han encontrado %s SC Hubs (Hub de control)\n", comHubPorts.size());

		for (portCount = 0; portCount < comHubPorts.size() && portCount < NET_CONTROLLER_MAX; portCount++) {

			myMgr->ComHubPort(portCount, comHubPorts[portCount].c_str()); 	//define the first SC Hub port (port 0) to be associated 
																			// with COM portnum (as seen in device manager)
		}
		
		if (portCount > 0) {
			//printf("\n I will now open port \t%i \n \n", portnum);
			myMgr->PortsOpen(portCount);				//Open the port

			for (size_t i = 0; i < portCount; i++) {
				IPort &myPort = myMgr->Ports(i);

				printf(" Port[%d]: state=%d, nodes=%d\n",
					myPort.NetNumber(), myPort.OpenState(), myPort.NodeCount());
			}
		}
		else {
			printf("Unable to locate SC hub port\n");

			msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key

			return -1;  //This terminates the main program
		}


		//Once the code gets past this point, it can be assumed that the Port has been opened without issue
		//Now we can get a reference to our port object which we will use to access the node 

		IPort &myPort = myMgr->Ports(0);

		for (int i = 0; i < myPort.NodeCount(); i++) {
			INode &Motor = myPort.Nodes(i);

			printf("   Node[%d]: type=%d\n", i, Motor.Info.NodeType());
			printf("            userID: %s\n", Motor.Info.UserID.Value());
			printf("        FW version: %s\n", Motor.Info.FirmwareVersion.Value());
			printf("          Serial #: %d\n", Motor.Info.SerialNumber.Value());
			printf("             Model: %s\n", Motor.Info.Model.Value());

		}


		INode &Motor = myPort.Nodes(0);		// Motor arquero 
		INode &Motor2 = myPort.Nodes(1);		// Arquero

		//The following statements will attempt to enable the node.  First,
		// any shutdowns or NodeStops are cleared, finally the node in enabled
		Motor.Status.AlertsClear();					//Clear Alerts on node 
		Motor.Motion.NodeStopClear();	//Clear Nodestops on Node  				
		Motor.EnableReq(true);					//Enable node 
		Motor2.Status.AlertsClear();					//Clear Alerts on node 
		Motor2.Motion.NodeStopClear();	//Clear Nodestops on Node  				
		Motor2.EnableReq(true);					//Enable node 

		double timeout = myMgr->TimeStampMsec() + TIME_TILL_TIMEOUT;	//define a timeout in case the node is unable to enable
																		//This will loop checking on the Real time values of the node's Ready status
		while (!Motor.Motion.IsReady()) {
			if (myMgr->TimeStampMsec() > timeout) {
				printf("Error: Timed out waiting for Node %d to enable\n", 0);
				msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
				return -2;
			}
		}

		//At this point the Node is enabled, and we will now check to see if the Node has been homed
		//Check the Node to see if it has already been homed, 
		if (Motor.Motion.Homing.HomingValid())
		{
			if (Motor.Motion.Homing.WasHomed())
			{
				printf("Motor %d has already been homed, current position is: \t%8.0f \n", 0, Motor.Motion.PosnMeasured.Value());
				printf("Rehoming Node... \n");
			}
			else
			{
				printf("Motor [%d] has not been homed.  Homing Node now...\n", 0);
			}
			//Now we will home the Node
			Motor.Motion.Homing.Initiate();

			timeout = myMgr->TimeStampMsec() + TIME_TILL_TIMEOUT;	//define a timeout in case the node is unable to enable
																	// Basic mode - Poll until disabled
			while (!Motor.Motion.Homing.WasHomed()) {
				if (myMgr->TimeStampMsec() > timeout) {
					printf("Node did not complete homing:  \n\t -Ensure Homing settings have been defined through ClearView. \n\t -Check for alerts/Shutdowns \n\t -Ensure timeout is longer than the longest possible homing move.\n");
					msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
					return -2;
				}
			}
			Motor.Motion.PosnMeasured.Refresh();		//Refresh our current measured position
			printf("Motor completed homing, current position: \t%8.0f \n", Motor.Motion.PosnMeasured.Value());
			printf("Soft limits now active\n");

			//printf("Adjusting Numberspace by %d\n", CHANGE_NUMBER_SPACE);
			//Motor.Motion.AddToPosition(CHANGE_NUMBER_SPACE);			//Now the node is no longer considered "homed, and soft limits are turned off
			//Motor.Motion.Homing.SignalComplete();		//reset the Node's "sense of home" soft limits (unchanged) are now active again

			Motor.Motion.PosnMeasured.Refresh();		//Refresh our current measured position
			printf("Numberspace changed, current position: \t%8.0f \n", Motor.Motion.PosnMeasured.Value());
		}
		else {
			printf("Motor[%d] has not had homing setup through ClearView.  The node will not be homed.\n", 0);
		}

		printf("Homing listo\n");
		

		Motor.Motion.MoveWentDone();						//Clear the rising edge Move done register

		Motor.AccUnit(INode::RPM_PER_SEC);				//Set the units for Acceleration to RPM/SEC
		Motor.VelUnit(INode::RPM);						//Set the units for Velocity to RPM
		Motor.Motion.AccLimit = ACC_LIM_RPM_PER_SEC;		//Set Acceleration Limit (RPM/Sec)
		Motor.Motion.VelLimit = VEL_LIM_RPM;				//Set Velocity Limit (RPM)

		printf("Moving Motor \t%zi \n", 0);

		Motor.Motion.MovePosnStart(MOVE_DISTANCE, false, false);
		while (!Motor.Motion.MoveIsDone()) {
			if (myMgr->TimeStampMsec() > timeout) {
				printf("Error: Timed out waiting for move to complete\n");
				msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
				return -2;
			}
		}
		Motor.Motion.MoveWentDone();


		// DETENCION ABRUPTA DEL MOVIMIENTO
		printf("Timepo Inicio: %8.0f \n",myMgr->TimeStampMsec());
		Motor.Motion.MovePosnStart(-MOVE_DISTANCE/2, false, false);
		while (!Motor.Motion.MoveIsDone()) {
			Motor.Motion.PosnMeasured.Refresh();
			if (Motor.Motion.PosnMeasured.Value() <= MOVE_DISTANCE/2) {
				Motor.Motion.NodeStop(STOP_TYPE_ABRUPT);
				break;
			}
			if (myMgr->TimeStampMsec() > timeout) {
				printf("Error: Timed out waiting for move to complete\n");
				msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
				return -2;
			}
		}
		printf("Timepo Detencion: %8.0f \n", myMgr->TimeStampMsec());


		Motor.Motion.MovePosnStart(6000 , false, false);
		while (!Motor.Motion.MoveIsDone()) {
			if (myMgr->TimeStampMsec() > timeout) {
				printf("Error: Timed out waiting for move to complete\n");
				msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
				return -2;
			}
		}


		Motor2.AccUnit(INode::RPM_PER_SEC);				//Set the units for Acceleration to RPM/SEC
		Motor2.VelUnit(INode::RPM);						//Set the units for Velocity to RPM
		Motor2.Motion.AccLimit = 10000;		//Set Acceleration Limit (RPM/Sec)
		Motor2.Motion.VelLimit = 4000;

		Motor2.Motion.MovePosnStart(-6400, false, false);
		while (!Motor2.Motion.MoveIsDone()) {
			if (myMgr->TimeStampMsec() > timeout) {
				printf("Error: Timed out waiting for move to complete\n");
				msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
				return -2;
			}
		}

		printf("Motor \t%zi Move Done\n", 0);

		Motor.Motion.PosnMeasured.Refresh();
		printf("Posicion actual del Carro: %8.0f \n", Motor.Motion.PosnMeasured.Value());
		msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key

		printf("Desabilitando Motor 1\n");
		Motor.EnableReq(false);
		printf("Desabilitando Motor 2\n");
		Motor2.EnableReq(false);


		
	}
	catch (mnErr& theErr)
	{
		//This statement will print the address of the error, the error code (defined by the mnErr class), 
		//as well as the corresponding error message.
		printf("Caught error: addr=%d, err=0x%08x\nmsg=%s\n", theErr.TheAddr, theErr.ErrorCode, theErr.ErrorMsg);

		msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key

		return 0;  //This terminates the main program
	}
		

	// Close down the ports
	myMgr->PortsClose();

	msgUser("Press any key to continue."); //pause so the user can see the error message; waits for user to press a key
	return 0;			//End program
}

