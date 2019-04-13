---
System and Java version
---
Win 7, 64 bits;
Java Ver. 1.8.0_131;

---
Installation
---

1. Unzip the archive.

2. Make sure to add the following to the path variable:
C:\Program Files\Java\jdk<jre_version>\bin;
C:\Program Files\Java\jdk<jre_version>\jre\bin;
C:\Program Files\Java\jdk<jre_version>\jre\bin\server;
C:\program file\java\jre<jre_version>;


---
To run the tool
---

The test-cases are seperated in different folders "usecases->_TC*->*-*". For each test-case, there is an input folder "in" to have input data: "historySCHED1.txt"-- GCL scheduling table; "msg.txt"-- frame size, period, frame type, etc.; "vls.txt"-- routing; "rate.txt"-- link rate.

1. Open the command line and change the directory to the root of the tool folder. Let's call this folder from now ARTIFACT_ROOT. 

2. Run one experiment using the command:
TSNNetCal.exe usecases\<test-case_name>   %There may be one or two layers of folders

For example, for running input files in "ORION+TC1", the command is:
TSNNetCal.exe usecases\_TC1 - random open windows (change overlapped situations)\1-1

3. After running the experiments, the results for each test-case can be found under the "out" folder ARTIFACT_ROOT\<test_case_name>\out.
The subfolders of the experiments results contain the "TmpWCPortDelay.txt" file and the "WCEndtoEndDelay.txt" files. 
"TmpWCPortDelay.txt" contains the worst-case delays of flows in each output port of the node (end system (ES)/switch (SW)).
"WCEndtoEndDelay.txt" provides the end-to-end worst-case latency (WCD) for each AVB flow along the path (including the multicast path) from the source ES to a destination ES.

The experiment results are obtained from "WCEndtoEndDelay.txt". Note that the WCD for the multicast flow is the maximum value of WCD delays to different destination ESes.

---
Source Code folder
1. gb_pr (ES syn) exepath
2. gb_pr (ES syn) filepath - debug
