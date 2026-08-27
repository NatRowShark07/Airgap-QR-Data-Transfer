This Github repo is for the iPhone offline web application part of the QR Data Transfer Protocol (QRDTP). It comprises the app that displays the authentication QR code to begin transmission, manages the transmission of QR codes, requests that codes be resent, and finally closes the process when all data is properly received and assembled.

QRDTP is a way to securely and rapidly transfer and wirelessly transfer data from one device to another via an optical airgap. The graphic below illustrates the steps which QRDTP follows to transfer files.

![AQRDT Flow Chart](AQRDT_Flow_Chart.png)

This system is currently impractical for large, uncompressed files due to the sheer number of QR codes required to transmit the full file. The primary use case is for small text documents and images to connect to older legacy devices which struggle to connect to the internet or devices where a wired connection is not practical. Some additional advantages to this system are its ease of use and authentication for security. Currently, this is a demo version which is very early in development.
