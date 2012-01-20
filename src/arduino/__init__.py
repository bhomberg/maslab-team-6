from arduino3 import *
from blargh import Blargh
from exceptions import ValueError
from multiprocessing import Pipe, Process
import time

def arduinoInterface(masterConn, inputConn, outputConn, arduinoWrapper):

    # Start the arduino wrapper
    arduinoWrapper.start()

    # Input from inputConn or outputConn should be a (cmd, arg) tuple
    def handleCommand(conn):
        cmd, arg = conn.recv()
        if (cmd == "IR"):
            # Send back the IR distance
            conn.send(arduinoWrapper.getIRSensorDist(arg))
        elif (cmd == "BUMP"):
            # Send back whether the bump sensor was hit or not
            conn.send(arduinoWrapper.getBumpSensorHit(arg))
        elif (cmd == "MOTOR"):
            motorNum, speed = arg
            # Set the motor speed via the wrapper
            arduinoWrapper.setMotorSpeed(motorNum, speed)
            conn.send("DONE")
        elif (cmd == "SERVO"):
            servoNum, angle = arg
            # Set the servo angle via the wrapper
            arduinoWrapper.setServoAngle(servoNum, angle)
            conn.send("DONE")
        else:
            # Raise a value error, because none of the possible inputs
            # were matched
            raise ValueError

    while True:
        if (masterConn.poll()):
            inp = masterConn.recv()
            if (inp == "KILL"):
                return 0
            else:
                raise ValueError
        if (inputConn.poll()):
            handleCommand(inputConn)
        if (outputConn.poll()):
            handleCommand(outputConn)

# Called from the master process to create the arduino interface process
def createArduinoInterface():
    inputChildConn, inputParentConn = Pipe()
    outputChildConn, outputParentConn = Pipe()
    masterChildConn, masterParentConn = Pipe()

    arduinoWrapper = ArduinoWrapper()

    proc = Process(target = arduinoInterface, args = (masterChildConn, inputChildConn, outputChildConn, arduinoWrapper))
    proc.start()

    return (masterParentConn, inputParentConn, outputParentConn)

class ArduinoInterfaceInputWrapper():
    def __init__(self, conn):
        self.conn = conn

    def getIRDist(self, irNum):
        self.conn.send(("IR", irNum))
        return self.conn.recv()

    def getBumpHit(self, bumpNum):
        self.conn.send(("BUMP", bumpNum))
        return self.conn.recv()

class ArduinoInterfaceOutputWrapper():
    def __init__(self, conn):
        self.conn = conn

    def setMotorSpeed(self, motorNum, speed):
        self.conn.send(("MOTOR", (motorNum, speed)))
        return self.conn.recv()

    def setServoAngle(self, servoNum, angle):
        self.conn.send(("SERVO", (servoNum, angle)))
        return self.conn.recv()

class ArduinoWrapper():
    # Initialize the arrays which will contain our sensors and such
    def __init__(self):
        # Create the Arduino object
        self.ard  = Arduino()
        # Clear all the lists
        self.mcs = []
        self.motors = []
        self.servos = []
        self.irSensors = []
        self.bumpSensors = []

        # Set up our specific sensors and actuators
        self.mcs.append(MotorController(self.ard, 18, 19))
        self.motors.append(Motor(self.ard, self.mcs[0]))
        self.motors.append(Motor(self.ard, self.mcs[0]))

        self.bumpSensors.append(BumpSensor(self.ard, 2))

    def start(self):
        self.ard.run()

    def stop(self):
        for motor in self.motors:
            motor.setValue(0)
        time.sleep(0.5)
        self.ard.stop();

    # Helper functions to add all of our components
    def addIRSensor(self, index):
        ir = IRSensor(self.ard, index)
        self.irSensors.append(ir)
        return ir
    def addBumpSensor(self, index):
        bump = BumpSensor(self.ard, index)
        self.bumpSensors.append(bump)
        return bump
    def addMotor(self):
        motor = Motor(self.ard)
        self.motors.append(motor)
        return motor
    def addServo(self, index):
        servo = Servo(self.ard, index)
        self.servos.append(servo)
        return servo
    def addMC(self, txPin, rxPin):
        mc = MotorController(self.ard, txPin, rxPin)
        self.mcs.append(mc)
        return mc

    # Helper functions to get/set things related to our actuators and sensors
    def getIRSensorDist(self, irNum):
        return self.irSensors[irNum].dist()
    def getBumpSensorHit(self, bumpNum):
        return self.bumpSensors[bumpNum].hit()
    def setMotorSpeed(self, motorNum, speed):
        self.motors[motorNum].setVal(speed)
    def setServoAngle(self, servoNum, angle):
        self.servos[servoNum].setAngle(angle)

# A wrapper class for an IR sensor
class IRSensor(AnalogSensor):
    def dist(self):
        # TODO: Map voltages to distances somehow
        return self.getValue()

# A wrapper class for a bump sensor
class BumpSensor(DigitalSensor):
    # Test for hit
    def hit(self):
        return self.getValue()
