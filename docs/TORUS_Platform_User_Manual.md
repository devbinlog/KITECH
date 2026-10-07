# TORUS Platform User Manual

> **버전:** 2.3.2.1

---

## TORUS Platform 사용자 매뉴얼

TORUS Platform User Manual Ver-2.3.2.1 

---

## 1. 소개

TORUS Platform의 개념과 아키텍처 구조, 주요 데이터 체계 및 환경 구축 방법과 적용 방안에 대해 간략히 소개합니다. 

---

### 1.1 TORUS Platform 소개
TORUS Platform(in T egrated devel O pment and ope R ation environment for digitalization and automation and intellectualization of man U facturing indu S try, 이하 TORUS Platform 혹은 Platform)은 생산.제조 현장의 이종 벤더 CNC나 산업용 통신 프로토콜로 연결된 생산 장비(이하 '비가공장비')등에 적용이 가능한 Application S/W를 위한 개발.운용 플랫폼 입니다. TORUS Platform은 단일 인터페이스를 통해 다양한 이종 벤더 CNC나 로봇, PLC 등의 비가공장비로부터 정보를 읽어오거나 쓸 수 있는 기능을 지원하며, 개별 Application S/W 간에 데이터를 교환하거나 System 내에서 원활히 동작하도록 제어하는 기능을 지원합니다. 또한 개발자들이 이러한 기능들을 손쉽게 이용하여 이종 벤더 CNC나 로봇, PLC에 적용할 수 있는 Application S/W를 개발할 수 있도록 LIB API등의 개발 환경을 제공합니다. 

---

### 1.2 TORUS Platform Architecture
TORUS Platform은 이종 벤더 CNC나 로봇, PLC 등의 생산.제조 현장의 장비들을 통합할 수 있도록 제작된 소프트웨어 플랫폼 입니다 . 전체 Architecture는 다음 <Fig 1>와 같습니다.

![image](./lib/NewItem486.png)
Fig 1 - TORUS Architecture 

---

### 1.3 TORUS Platform의 Data 주소 체계
TORUS Platform은 각 Application들 간에 데이터를 서로 교환할 수 있도록 지원합니다. 이에, 각 App들이 서로 교환하고자 하는 데이터를 식별하고 지칭하기 쉽도록 하기 위해 개별 데이터의 주소 체계와 기본 사용 규칙을 규정하여 지원합니다 . Platform 기반의 각 App 간 데이터 공유를 위해서는 다음의 규정을 준수해야 합니다. 

---

#### 1.3.1 Data 주소 체계 기본 구조

Platform에서 지원하는 데이터 주소체계의 기본 구조는 다음과 같습니다.
- Data 주소 체계 구조
{ Protocol}://{Provider_name}/{Address}?{Filter}

| 이름 | 설명 | 예 |
| ------------- | ------------------------- | --------------------------------------- |
| Protocol | 제공자 내부의 데이터 분류 | “Machine”, “data”, “file” |
| Provider_name | 데이터 제공자(소유자) 이름 ex: App이름 | “Toolmgr”, “Machine.Monitor”, “machine” |
| Address | 제공자 내부 데이터 구조에 따른 주소 | “Mainview/ID_1”, “channel/axis” |
| Filter | 데이터를 상세히 식별할 수 있는 세부 조건 | |

<표 2 - 플랫폼 Data Address 체계>
- 예
data://Machine_monitor.torus.co.kr/mainview/actToolname data://machine/channel/axis/machinePos?channel=1&axis=1 

---

#### 1.3.2 Data 주소 체계 기본 사용 규칙

Platform에서 사용하는 data 주소 체계는 다음과 같은 기본 규칙을 따릅니다.

| 예> data://Machine_monitor.torus.co.kr/mainview/actToolname data://machine/channel/axis/machinePos? machine=1&channel=1&axis=1 ↓ ↓ ↓ ↓ protocol provider name 데이터 주소 필터 |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- Uri 표준 표기법을 따릅니다. (RFC3986)
- TORUS Platform은 protocol로 "data"만 허용합니다.
- provider_name은 데이터 소유자를 유일하게 식별할 수 있어야 합니다. 보통은 위의 첫 번째 예와 같이 데이터 소유자의 대표 웹 사이트 URL을 이용합니다.
- "?" 표시 뒤 부분에 표기되는 "필터"는 그 앞에 명시된 데이터 주소를 구체화하기 위해 사용됩니다. 데이터 주소 자체로 데이터를 식별할 수 있으면 사용하지 않아도 됩니다.
- 만약 지칭하는 데이터가 데이터베이스 테이블에 있는 데이터인 경우에는 “ ? ” 표시 뒤에 데이터베이스 Query를 추가할 수 있습니다. 만약 Query가 없다면, 식별 가능한 데이터 테이블의 row 전체 혹은 테이블 전체를 지칭하게 됩니다.
- “ ? ” 표시 뒤에 App 간에 약속한 문자나 기호를 추가할 수 있습니다. 이는 통신하는 App 서로 간의 약속을 통해 임의로 정할 수 있습니다.
Machine Data Model(NC 데이터)의 경우, List type 데이터를 명확히 식별하기 위해 “ ? ” 표시 뒤 부분에 데이터를 특정할 수 있는 정보를 추가할 수도 있습니다.  이는 ' 1.3 .3 NC Data주소 체계 사용 규칙' 의 내용을 참고하십시오.
- NC 데이터 어드레스 지정 시, "machine=xx" 필터는 machineList.xml에 정의된 장비 ID를 지정합니다.
다중 장비 접속을 위해서는 반드시 "machine" 필터를 지정해야 합니다. 다만, machineList.xml에 여러 장비 정보가 설정되었더라도 실제 장비는 1대만 연결될 경우이거나 machineList.xml에 장비 1대만 설정되어 있고, 실제 그 장비가 연결된 경우에 "machine" 필터를 지정하지 않으면, 플랫폼 내부에서 자동으로 유일하게 연결된 장비를 지칭하도록 되어 있습니다. 자세한 사항은 '3.1.2 가공장비 리스트 작성' 을 참고 하시기 바랍니다. 

---

#### 1.3.3 NC Data 주소 체계 사용 규칙

TORUS Platform에서 지원하는 Machine Data Model(NC 데이터)의 주소체계는 다음과 같은 사용 규칙을 따릅니다. 공작기계는 여러 개의 Channel, 여러 개의 축, 여러 개의 Tool 등을 가질 수 있습니다. 플랫폼에서는 이를 List type Data로 표현합니다. 목차 4.1.1의 <표 6>에 표시된 Machine Data Model 계층구조 중 "axis [ ]" 처럼 데이터 이름에 "[ ]" 표기가 추가된 데이터가 List type Data 입니다. List type Data는 Uri 주소 표기 방식으로 NC 데이터를 지칭할 때, 명확한 주소 식별을 위해 "Filter" 정보를 주소 표기에 추가해야 합니다. 주소 표기 방법은 '1.3.2 Data 주소 체계 기본 사용 규칙' 에서 설명한 바와 같이 데이터 어드레스 뒤에 "?" 표기 후 입력합니다. 다음의 예시와 <표 3>의 내용을 참고하시기 바랍니다.
-
-

-

-

-

| 표기 | 설명 | 예 |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| & | 각 Filter 요소를 구분하는 역할 각 Filter 간 AND 관계임을 표시 | channel=1&axis=1 → 1번 channel의 1번 축 |
| - | 연속된 데이터를 지정하는 역할 | channel=1&axis=1-5 → 1번 channel의 1번 축부터 5번 축까지 |
| , | 불연속 데이터를 지정하는 역할 | Channel=1&axis=1,3,6 → 1번 channel의 1번, 3번, 6번 축 |
| 응용 예 | data://machine/channel/axis/machinePosition?channel=1&axis=1-3,7 → 1번 channel의 1번 축부터 3번 축까지 그리고 7번 축에 대한 값 주의) - 여러 장비가 Platform에 연결된 상태에서 "machine"을 필터로 정의하지 않으면 자동으로 "machine=0"로 지정함 (오류 발생) - 단일 장비가 Platform에 연결된 상태에서 "machine"을 필터로 정의하지 않으면 플랫폼에서 자동으로 해당 장비의 ID를 지정해줍니다. data://machine/channel/axis/machinePosition?channel=1-2&axis=1,3-5 → 1번 channel의 1번 축과 3번 축부터 5번축까지 그리고, 2번 channel의 1번 축과 3번 축부터 5번축까지 ("machine"을 필터로 정의하지 않으면 자동으로 "machine=1"로 지정함) data://machine/channel/numberOfAlarms?machine=2&channel=1 → 2번째 machine의 channel 1번에 대한 알람 개수 정보 | |

<표 3 - Filter 정보 사용 방식> 

---

### 1.4 TORUS Platform 환경 구축
TORUS Platform을 구동하고, TORUS Platform 기반으로 동작하는 이종 벤더 CNC용 Application S/W를 개발하기 위해서는 연결 대상 NC가 어떤 NC 인가에 따라 다음 <표 1>의 S/W들을 기본적으로 설치해야 합니다.

| S/W 이름 | 내용 |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Visual Studio 2012 이상 | Redistributable Package(재배포 가능 패키지)는 Visual C++ 2012이 설치되지 않은 컴퓨터에서 Visual C++로 개발된 응용 프로그램을 실행하는 데 필요한 Visual C++ 라이브러리의 런타임 구성 요소를 설치하는 역할을 합니다. |
| TORUS SDK LIB | SIEMENS, FANUC, CSCAM MITSUBISHI NC에 대한 통합 통신 LIB 및 HMI App 개발용 API가 지원됩니다. "플랫폼설치경로\Example_VS19\Api" 폴더에 있습니다. . |
| SIEMENS Sinutrain | SIEMENS NC 에뮬레이션 프로그램으로, PC 상에서 SIEMENS NC와 가상으로 통신을 연결하여 데이터를 읽고 쓸 수 있도록 하는 S/W 프로그램 입니다. SIEMENS NC와 직접 연결할 수 있으면 설치하지 않아도 됩니다. |
| FANUC NC GUIDE | FANUC NC 에뮬레이션 프로그램으로, PC 상에서 FANUC NC와 가상으로 통신을 연결하여 데이터를 읽고 쓰는데 필요한 S/W 프로그램 입니다. FANUC NC와 직접 연결할 수 있으면 설치하지 않아도 됩니다. |
| CSCAM NC Emulator | CSCAM NC 에뮬레이션 프로그램으로, PC 상에서와 CSCAM NC와 가상으로 통신을 연결하여 데이터를 읽고 쓰는데 필요한 S/W 프로그램 입니다. CSCAM NC와 직접 연결할 수 있으면 설치하지 않아도 됩니다. |
| MITSUBISHI NC Trainer2 | MITSUBISHI NC 에뮬레이션 프로그램으로, PC 상에서 MITSUBISHI NC와 가상으로 통신을 연결하여 데이터를 읽고 쓸 수 있도록 하는 S/W 프로그램 입니다. MITSUBISHI NC와 직접 연결할 수 있으면 설치하지 않아도 됩니다. |
| KCNC TENUX Emulator | KCNC NC 에뮬레이션 프로그램으로, PC 상에서 KCNC NC와 가상으로 통신을 연결하여 데이터를 읽고 쓰는데 필요한 S/W 프로그램 입니다. KCNC NC와 직접 연결할 수 있으면 설치하지 않아도 됩니다. |

<표 1 - 기본 설치 필요 S/W> 

---

#### 1.4.1 SIEMENS 기반 TORUS 구동 및 App 개발환경 구축

'1.4 TORUS Platform 환경 구축' 에 나온 기본 설치 필요 S/W 이외에 SIEMENS 기반의 개발환경 구축을 위해 아래의 소프트웨어를 추가로 설치해야 합니다. - 직접 NC와 연결할 경우, SIEMENS SINUMERIK Operate 4.7 이상 - SIEMENS 통신 LIB ("3.2.3 설치 후 라이브러리 파일 업데이트" 참고) 자세한 설치 방법은 SIEMENS 홈페이지 혹은 SIEMENS 자료를 참고하시기 바랍니다 . 

---

#### 1.4.2 FANUC 개발환경 구축

'1.4 TORUS Platform 환경 구축' 에 나온 기본 설치 필요 S/W 이외에 FANUC 기반의 개발 환경 구축을 위해 아래 사항이 추가로 필요 합니다. - FANUC FOCAS LIB  ( '2.3 설치 후 라이브러리 파일 업데이트' 참고) 

---

#### 1.4.3 MITSUBISHI 개발환경 구축

'1.4 TORUS Platform 환경 구축' 에 나온 기본 설치 필요 S/W 이외에 MITSUBISHI 기반의 개발환경 구축을 위해 아래의 소프트웨어를 추가로 설치해야 합니다. - MITSUBISHI Communication Software FCSB1224W000 자세한 설치 방법은 MITSUBISHI 홈페이지를 참고하시기 바랍니다 . 

---

#### 1.4.4 CSCAM 개발환경 구축

'1.4 TORUS Platform 환경 구축' 에 나온 기본 설치 필요 S/W 이외에 CSCAM NC 기반의 개발환경 구축을 위해 추가로 설치해야 할 소프트웨어 없습니다. CSCAM NC와 연동하기 위해 필요한 소프트웨어와 라이브러리 일체는 TORUS Platform 설치 시에 자동으로 설치됩니다. 

---

#### 1.4.5 KCNC 개발환경 구축

'1.4 TORUS Platform 환경 구축' 에 나온 기본 설치 필요 S/W 이외에 KCNC TENUX 기반의 개발환경 구축을 위해 추가로 설치할 소프트웨어는 없습니다. KCNC TENUX와 연동하기 위해 필요한 소프트웨어와 라이브러리 일체는 TORUS Platform 설치 시에 자동으로 설치됩니다. 

---

### 1.5 TORUS Platform 적용 방법
Application S/W에서 Platform의 기능을 사용하기 위한 대표적인 방법들과 참고할 내용이 기술된 매뉴얼의 목차를 설명합니다. 

---

#### 1.5.1 CNC의 데이터를 읽거나 쓰기 위해서는 어떻게 해야 하는가

Application에서 NC의 데이터에 접근하여 값을 읽거나 쓰기 위해서는 NC의 데이터가 모여있는 Machine Data Model에 접근해야 합니다. Machine Data Model은 공작기계의 현재 상태 정보 및 일부 설정 정보들과 관련된 NC 데이터가 모두 저장되어 있는 데이터 모델 입니다. Machine Data Model은 사용자가 원하는 데이터에 대해 항상 최신 값으로 유지됩니다. Platform은 Machine Data Model에 접근하여 NC 정보를 읽고 쓸 수 있는 함수들을 지원합니다. Machine Data Model에 저장된 NC 데이터는 읽기 기능만 지원되는 데이터도 있고, 읽기와 쓰기가 모두 지원되는 데이터들도 있습니다. 만약 읽기만 지원되는 데이터들에 값 쓰기를 시도하면 해당 함수에 대해 Error가 반환 됩니다. Machine Data Model에 대한 사항은 “ 5.1 Machine Data Model 정의 ” 의 내용을 참고하십시오 Machine Data Model 내에서 원하는 개별 데이터를 지칭하고 식별하는 방법은 ' 1.3 TORUS Platform의 Data 주소 체계' 의 내용을 참고하십시오. Machine Data Model을 통해 NC의 데이터를 읽고 쓰는 방법은 ' 7 .2.2 Data Access API' 의 내용을 참고하십시오. 

---

#### 1.5.2 다른 Application의 데이터를 읽거나 쓰려면 어떻게 해야 하는가

Platform은 Application과 Application 간의 데이터 교환을 지원합니다. 다만 이때에는 각 Application이 외부에 제공하기로 설정한 데이터에 한 해 외부 Application의 접근이 허용됩니다. 원하는 Application과 데이터 교환을 원한다면 우선 해당 Application이 어떤 데이터를 제공하고 있는지 설정을 확인할 필요가 있습니다. (Application 정보의 설정 방법 등은 추후 상세히 정의될 예정입니다) 다른 Application이 제공하는 데이터를 지칭하고 식별하는 방법은 ' 1.3 TORUS Platform의 Data 주소 체계' 의 내용을 참고하십시오. 다른 Application이 제공하는 데이터를 읽거나 쓰는 방법은 ' 7 .2.2 Data Access API' 의 내용을 참고하십시오. 

---

#### 1.5.3 다른 Application을 실행시키려면 어떻게 해야 하는가

Platform은 다른 Application에 명령을 전달하여 해당 Application을 실행시킬 수 있는 API 함수를 지원합니다 . 또한 다른 Application에 전달할 수 있는 명령(COMMAND)도 정의되어 있습니다. 다른 Application에 전달할 수 있는 명령의 종류나 함수의 사용법을 확인하려면 '7.2.4 Application Control' 의 내용을 참고하십시오. 

---

#### 1.5.4 다른 Application으로부터 명령을 수신하려면 어떻게 해야 하는가

다른 Application에서 전달한 명령을 수신하고 이를 처리하기 위해서는 전달될 각 명령에 대한 처리 함수를 미리 정의해놓아야 합니다. Platform은 이러한 명령을 수신하여 수행할 함수의 Prototype을 미리 정의해놓고 있습니다. 또한 Prototype 형태로 정의/구현한 함수를 명령 처리 루틴으로 등록하는 기능을 함수 형태로 지원합니다. 다른 Application로부터 전달받을 수 있는 명령의 종류를 확인하려면 ' 7 .2.8 Event Handler ' 의 내용을 참고하십시오. 다른 Application이 전달한 명령을 수신하고 처리하는 방법은 ' 7 .2.2 Data Access API' 및 '7.2.4 Application Control' 의 내용을 참고하십시오. 

---

## 2. TORUS Platform 설치하기

TORUS Platform 설치 방법 및 관련된 사항을 참고 할수 있습니다. 

---

### 2.1 설치 사양
2. TORUS Platform 설치하기 

TORUS Platform 설치를 위한 H/W 사양은 아래와 같습니다. [ 사양 ]

| 항목 | 사양 | 비고 |
| ------------ | -------------------------------------------------------- | ------------------------------------------------------ |
| 운영 체제 ( OS ) | - Microsoft Windows 7 이상 [32/64bit 계열] | Windows 10 권장 |
| CPU | - ATOM Processor x-series (4 Core, 1.3GHz, 1MB Cache) 이상 | Intel Core i series 이상 권장 |
| Memory | - 1GB 이상 | 4GB 이상 권장 |
| 저장장치 | - 64 GB 이상 | SSD 128GB 이상 권장 |
| 통신 | - 1Gbps Ethernet Port 1개 이상 지원 - USB Port 1개 이상 지원 | - 1 Gbps Ethernet Port 2개 이상 지원 권장 - USB Port 3개 이상 지원 |

---

### 2.2 설치 순서
2. TORUS Platform 설치하기 

TORUS Platform 설치 순서는 아래와 같습니다. 주의> Microsoft .NET Framework 3.5가 설치 되어 있지 않은 경우 TORUS Platform 설치 후 인터넷 다운로드 경로로 자동 연결 됩니다. 인터넷 연결 확인 후 설치를 진행 바랍니다. (함께 설치되는 기본 Sample Application을 위해 설치가 필요합니다.) ①  설치 파일 ( TORUS.exe )을  실행합니다. ②  설치를 진행하는 동안 사용할 언어를 선택합니다. ( 제공 언어 : 한국어 , 영어 ) "English" 또는 "Korean" 을 선택 후 "OK" 를 클릭합니다.

![image](./lib/NewItem458.png)
③ TORUS Platform 설치를 시작합니다. "다음" 버튼을 클릭합니다.

![image](./lib/NewItem459.png)
④ TORUS Platform이 설치될 경로를 지정합니다.

![image](./lib/NewItem460.png)
⑤ TORUS Platform 설치가 진행됩니다. - Visual C++ 런타임 라이브러리  ( C++ 2010 , 2012 ) 설치 후 Platform 구성 요소가  설치 됩니다. ( 컴퓨터 사양에 따라 설치됩니다. 32Bit / 64Bit ) [  Microsoft Visual C++ 2010 64Bit 예제 화면 ] - 동의함 클릭 후 설치를 진행 합니다.

![image](./lib/NewItem462.png)
[  Microsoft Visual C++ 2012 64Bit 예제 화면 ] - 동의함 클릭 후 설치를 진행 합니다.

![image](./lib/NewItem463.png)
[ TORUS Platform 설치 중 화면 ]

![image](./lib/NewItem461.png)
⑥ TORUS Platform 설치 완료되었습니다.

![image](./lib/NewItem465.png)
마침 클릭 시 Microsoft .NET Framework 3.5 설치가 안 되어 있는 경우 자동으로 다운로드 링크가  연결됩니다. 다운 로드 후 설치 바랍니다. [ 다운 로드 경로 ] Korean - https://www.microsoft.com/ko-kr/download/details.aspx?id=21 English - https://www.microsoft.com/en-US/download/details.aspx?id=21

![image](./lib/NewItem466.png)

---

### 2.3 설치 후 라이브러리 파일 업데이트
2. TORUS Platform 설치하기 

TORUS Platform 설치 후 CNC 사양에 따른 통신 라이브러리를 업데이트 해주시기 바랍니다.

| CNC | 파일 형식 | 원본 경로 | 복사 경로 |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Siemense v4.5 v4.7 v4.8 v4.9 | *.dll | "MyHMI Install Drive"\hmisl\siemens\sinumerik\hmi\base\~ "MyHMI Install Drive"\hmisl\siemens\sinumerik\hmi\osal\ace\bin\~ "MyHMI Install Drive"\hmisl\siemens\sinumerik\hmi\osal\qt\bin\~ 위 3가지 경로에 있는 dll 혹은 xml 파일들을 복사해야 합니다. | 아래 2가지 중 하나를 선택합니다. 1) "Platform설치경로\Binary\nc_lib\siemens"에 복사합니다. 2) 임의의 폴더에 복사합니다. 이 경우 해당 폴더 경로를 MachineList의 exDllPath 속성에 저장하여야 합니다. ('3.1.2 가공장비 리스트 작성' 참조) |
| *.xml | "Platform설치경로\Binary\"에 복사합니다. | | |
| Fanuc | *.dll | FOCAS2 Library\Fwlib\~ 위 경로에 있는 dll 파일들을 복사해야 합니다. | 아래 2가지 중 하나를 선택합니다. 1) "Platform설치경로\Binary\nc_lib\fanuc"에 복사합니다. 2) 임의의 폴더에 복사합니다. 이 경우 해당 폴더 경로를 MachineList의 exDllPath 속성에 저장하여야 합니다. ('3.1.2 가공장비 리스트 작성' 참고) |
| Mitsubishi | Mitsubishi는 "MITSUBISHI Communication Software FCSB1224W000"가 TORUS Platform이 구동되는 컴퓨터에 설치되어 있어야 합니다. | | |
| K-CNC | TORUS Platform이 기본 지원하므로 별도의 라이브러리 업데이트 절차가 필요 없습니다. | | |
| OPC-UA | OPC-UA 옵션이 설치된 Siemens CNC에 연결된 경우에만 정상동작합니다.(추후 대상 CNC 확대 예정) TORUS Platform이 기본 지원하므로 별도의 라이브러리 업데이트 절차가 필요 없습니다. | | |
| MTConnect | MTConnect 옵션이 설치된 Mitsubishi CNC에 연결하는 경우에만 정상동작합니다.(추후 대상 CNC 확대 예정) TORUS Platform이 기본 지원하므로 별도의 라이브러리 업데이트 절차가 필요 없습니다. | | |

---

## 3. TORUS Platform 설정과 실행/종료

TORUS Platform LIB를 이용하여 개발한 Application을 테스트하거나 실행 중 디버깅을 하기 위해서는 다음의 내용을 참고하시기 바랍니다. 

---

### 3.1 플랫폼 설정 파일 작성 
3. TORUS Platform 설정과 실행/종료 

TORUS Platform을 실행하기 전에 몇 가지 설정할 사항들이 있습니다. 다음 목차의 내용을 확인하시기 바랍니다. 

---

#### 3.1.1 Application 등록정보 파일
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- Application 등록정보 설정
Application 등록정보 파일 내의 속성 값들을 확인합니다. 반드시 다음의 속성 값은 설정되어 있어야 합니다. 주1. Application 등록정보의 각 속성들의 의미는 “ 4.1.1 Application 등록정보의 구성 속성들 ” 을 참고하면 됩니다 주2. 현재는 기본 항목만 설정하면 됩니다. (추후, 설정할 기본 항목이 늘어날 수 있습니다) - App name - App ID - Version - App File “ App ID ” 에 설정된 GUID값은 Application 등록정보 파일에 설정한 값과 Application의 Source Code에 코딩된 값이 동일해야 합니다. 이를 사전 확인하십시오 . 모든 속성들의 내용에 대한 확인이 끝나면, Application 등록정보 파일을 미리 정해진 폴더에 복사해야 합니다. 현재는 복사할 경로가 “ "Platform설치경로\Binary \ application\ ” 입니다. ※ 추후, 경로가 특정 위치로 고정되거나 수정 될 수 있습니다 . 

---

#### 3.1.2 가공장비 리스트 (MachineList) 작성
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- 가공 장비 리스트 속성 설정
TORUS Platform 은 다중 장비 연결을 지원하며 여러 가공장비들과 연결하기 위한의 속성 정보를 리스트로 관리합니다. ■ 가공 장비 리스트 파일 작성 플랫폼에 연결되는 장비들의 속성을 "machineList.xml"에 저장하고 있습니다. 파일은 "Platform설치경로\Binary\" 에 있습니다. 파일 내에 정의된 속성 정보는 다음의 예시와 같습니다.

| <MachineList> <NCmachine activate="false" name="fanuc 1호기" id="1" vendorcode="fanuc" address="192.168.0.3" port="8193" exdllpath="../../ex_dll/fanuc"/> <NCmachine activate="true" name="kcnc 1호기" id="2" vendorcode="kcnc" address="127.0.0.1" port="3000"/> <NCmachine activate="false" name="fanuc1" id="3" vendorcode="fanuc" connectcode="default" address="localhost" port="8193" ncversioncode="default" toolsystem="default" username="" password="" exdllpath="../../ex_dll/fanuc"/> </MachineList> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

속성 정보의 구조는 다음과 같습니다.

| 속성정보 필드 | 설명 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| activate | 유효한 연결 여부를 확인합니다. 값이 "true" 이면 해당 필드에 기술된 장비에 통신 연결을 시도합니다. |
| name | 해당 장비의 이름입니다. 장비를 구분하는데 사용할 수 있습니다. |
| id | 해당 장비의 ID입니다. 중복된 ID가 있을 경우, 중복 ID 중에 먼저 기록된 장비에만 연결합니다. 유효한 값 : 1 이상의 정수 |
| vendorCode | 접속하려는 장비에 장착된 CNC의 제조사입니다. 유효한 값 : ※ 대소문자를 구분하지 않습니다. 1) Fanuc 2) Siemens 3) CSCAM 4) Mitsubishi 5) Kcnc 6) Mazak |
| address | 장비에 연결하기 위한 주소를 입력합니다. ※ MyHMI를 통한 Siemens 연결시에는 무시되는 값입니다. 실제 CNC에 연결되는 것은 MyHMI이고 플랫폼은 MyHMI에 연결합니다. |
| port | 장비에 연결하기 위한 포트를 입력합니다. ※ MyHMI를 통한 Siemens 연결시에는 무시되는 값입니다. 실제 CNC에 연결되는 것은 MyHMI이고 플랫폼은 MyHMI에 연결합니다. |
| exDllPath (optional) | 장비 연결에 필요한 외부 라이브러리 파일이 위치한 경로입니다. 입력하지 않으면 기본 경로값을 사용합니다. Fanuc 기본 경로 : Platform설치경로\Binary\nc_lib\fanuc Siemens 기본 경로 : Platform설치경로\Binary\nc_lib\siemens |
| connectCode (optional) | 장비 연결 방식을 입력합니다. 입력하지 않으면 "default"값을 사용합니다. 유효한 값 : ※ 대소문자를 구분하지 않습니다. 1) default (각 vendor별 기본 연결 방식 사용): Fanuc→Ethernet, Mitsubishi→Ethernet, Kcnc→Ethernet, Siemens→MyHMI, Mazak→MTConnect 2) Ethernet (Fanuc, Mitsubishi, Kcnc) 3) OPCUA (Siemens) ※ Username/Password 인증방식만 사용가능합니다. 4) HSSB (Fanuc) 5) MyHMI (Siemens) 6) MTConnect (Mitsubishi) ※ OPC-UA 연결 시 인증관련 파일을 "Platform설치경로\Binary\nc_opcua\"에 생성합니다. (폴더가 없을 시 자동 생성됨) OPC-UA 통신 연결 시, 기존에 생성된 인증파일을 우선 사용하므로 비밀번호나 장비를 변경을 하고나서 OPC-UA Server에 접속이 되지 않는 경우 "Platform설치경로\Binary\nc_opcua\" 폴더를 삭제하여 기존 인증파일을 제거하고 재 접속하시기 바랍니다. |
| ncVersionCode (optional) | 장비 버전을 입력합니다. 일부 vendor는 연결하려는 장비의 버전을 지정해 주어야 합니다. 입력하지 않으면 "default"값을 사용합니다. 유효한 값 : ※ 대소문자를 구분하지 않습니다. 1) default (각 vendor별 기본 버전 사용) Mitsubishi→MitsubishiM800M, Siemens→Siemens49 2) MitsubishiM700M 3) MitsubishiM700L 4) MitsubishiM800M 5) MitsubishiM800L 6) Siemens47 (MyHMI v4.7 사용시) 7) Siemens48 (MyHMI v4.8 사용시) 8) Siemens49 (MyHMI v4.9 사용시) |
| toolSystem (optional) | Fanuc에 연결할 경우 사용할 tool system을 입력합니다. 입력하지 않으면 "default"값을 사용합니다. 유효한 값 : ※ 대소문자를 구분하지 않습니다. 1) default (기본 Tool 기능) 2) ToolLife (Tool Life Management) 3) ToolManager (Tool Management) |
| username (optional) | OPC-UA를 통해 장비와 연결하는 경우에 사용할 Username입니다. |
| password (optional) | OPC-UA를 통해 장비와 연결하는 경우에 사용할 Password입니다. |

■ 가공 장비 리스트 파일 저장 위치 작성한 파일은 " "Platform설치경로\Binary\ "에 저장하면 됩니다. ■ 주의 사항 플랫폼이 설치된 HMI에 여러 대의 장비를 연결하고자 할 경우에는 반드시 machineList.xml 파일의 장비 연결 속성 정보를 확인하고 장비 구성에 맞게 파일의 내용을 변경해야 합니다. 

---

#### 3.1.3 비 가공장비 클라이언트 리스트 작성 
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- 비 가공장비 리스트 설정
TORUS Platform은 복수의 비 가공 장비 연결을 지원하며, 여러 비 가공장비 연결 정보와 속성을 리스트로 관리 합니다. ■ 연결된 비 가공 장비 리스트 작성 플랫폼에 연결되는 비 가공장비들의 속성을 "DeviceList.xml"에 저장하고 있습니다. 파일은 "플랫폼 실행 디렉터리"에 있습니다. 파일 내에 정의된 속성 정보는 다음의 예시와 같습니다.

| <DeviceList> <Attribute Activate="on" Device_ID="1" Device_protocol="1" Device_IP="192.168.164.1" Device_Port="502" Username="robotClient" Password="SUNRISE" exDllPath=""/> <Attribute Activate="on" Device_ID="2" Device_protocol="1" Device_IP="10.217.181.56" Device_Port="6060" Username="Client" Password="SUNRISE" exDllPath=""/> </DeviceList> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

속성 정보의 구조는 다음과 같습니다.

| 속성정보 필드 | 설명 |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Activate (optional) | 연결 시도 여부 확인용 필드 값이 "on" 이면 해당 필드에 기술된 장비에 통신 연결을 시도합니다. 값이 "off" 이면 해당 필드에 기술된 장비는 통신 연결을 시도하지 않습니다. 이 속성 정보가 없을 경우, 해당 필드에 기술된 장비는 무조건 통신 연결을 시도합니다. |
| ID | 해당 장비의 ID. 숫자를 부여함 '0' 값은 사용할 수 없습니다. 중복된 ID가 있을 경우, 장비 통신 연결을 시작하지 않습니다. |
| Device_protocol | 장비와 연결하기 위해 필요한 통신 프로토콜을 지정합니다. 미리 정의된 번호를 입력합니다. 현재 TORUS Platform에서 지원하는 비가공장비용 통신 프로토콜과 프로토콜 번호는 다음과 같습니다. 서버로 구분된 프로토콜은 지정할 수 없습니다. (서버는 TORUS Platform에서 구동하는 서버를 의미합니다) > Modbus TCP Client : 1 > Modbus TCP Server : 2 > Ethernet/IP : 3 > CC-LINK/IE : 4 > MQTT : 5 ※ Ethernet/IP, CC-LINK/IE, MQTT는 추후, 추가될 예정입니다. . |
| Device_IP | 장비 측 IP Address |
| Device_Port | 장비 측 PORT 번호 |
| Username (option) | 장비와 연결하기 위해 필요한 User ID 입니다. 옵션입니다. User ID가 없으면 지정하지 않아도 됩니다. |
| Password (optional) | 장비와 연결하기 위해 필요한 PASS WORD 입니다. 옵션입니다. PASS WORD가 없으면 지정하지 않아도 됩니다. |
| exDllPath (optional) | 장비와 연결하기 위해 필요한 외부 Lib 경로 입니다. 필요없으면 지정하지 않아도 됩니다. 만약 지정하게 되면, 여기에 지정한 경로에서 외부 Lib 파일을 검색합니다. 만약 지정하지 않으면 찾지 않거나, 구동 중 필요하면 TORUS Platform 설치 경로에서 검색합니다. |

■ 비 가공장비 리스트 파일 저장 위치 작성한 파일은 " "Platform설치경로\Binary\ "에 저장하면 됩니다. ■ 주의 사항 TORUS Platform에 연결된 비가공장비와 연결하고자 할 경우에는 반드시 DeviceList.xml을 실제 연결된 상태에 맞춰 설정해야 합니다. 또한 각 App에서 비가공장비와 연결하려고 할 때에는 DeviceList.xml 파일의 장비 연결 속성 정보를 확인하고 장비 구성에 맞게 각 App의 mapping table 내용을 변경 해야 합니다. ( '3.1.5 비 가공장비 어드레스 매핑 테이블 작성' 부분 참고) 

---

#### 3.1.4 비 가공장비 서버 리스트(산업용 통신 서버 리스트) 작성
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- 비 가공장비 서버 리스트(산업용 통신 서버 리스트) 설정
TORUS Platform은 다양한 산업용 통신 프로토콜 서버를 운영할 수 있습니다. 그러므로 TORUS Platform는 구동할 서버 속성을 리스트로 관리하고 있습니다. TORUS Platform에서 구동할 비 가공장비 서버에 대한 정보 설정은 다음과 같습니다. ■ TORUS Platform에서 서비스하는 비 가공장비 서버 리스트 (산업용 통신 서버 리스트) 속성 설정 TORUS Platform은 복수의 산업용 통신 서버를 구동할 수 있습니다. 그러므로 플랫폼이 구동 가능한 산업용 통신 서버들의 속성을 "DeviceCommSvrList.xml"에 저장하고 있습니다. 파일은 "플랫폼 실행 디렉터리"에 있으며, 파일 내에 정의된 속성 정보는 다음의 예시와 같습니다.

| <DeviceCommServerList> <Attribute Activate="on" DevCommSvr_ID="1" DevCommSvr_protocol="2" DevCommSvr_IP="127.0.0.1" DevCommSvr_Port="502" Username="OpcUaClient" Password="SUNRISE" exDllPath=""/> <Attribute Activate="off" DevCommSvr_ID="2" DevCommSvr_protocol="2" DevCommSvr_IP="10.217.181.56" DevCommSvr_Port="4840" Username="OpcUaClient" Password="SUNRISE" exDllPath=""/> </DeviceCommServerList> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

속성 정보의 구조는 다음과 같습니다.

| 속성정보 필드 | 설명 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Activate | 연결 시도 여부 확인용 필드 값이 "on" 이면 해당 필드에 기술된 장비에 통신 연결을 시도합니다. 값이 "off" 이면 해당 필드에 기술된 장비는 통신 연결을 시도하지 않습니다. 이 속성 정보가 없을 경우, 해당 필드에 기술된 장비는 무조건 통신 연결을 시도합니다. |
| DevCommSvr_ID | TORUS Platform에서 구동하는 서버의 ID. 숫자를 부여함 '0' 값은 사용할 수 없습니다. 중복된 ID가 있을 경우, 서버를 시작하지 않습니다. |
| DevCommSvr_protocol | 장비와 연결하기 위해 필요한 통신 프로토콜을 지정합니다. 미리 정의된 번호를 입력합니다. 현재 TORUS Platform에서 지원하는 비가공장비용 통신 프로토콜과 프로토콜 번호는 다음과 같습니다. 클라이언트로 구분된 프로토콜은 지정할 수 없습니다. > Modbus TCP Client : 1 > Modbus TCP Server : 2 > Ethernet/IP : 3 > CC-LINK/IE : 4 > MQTT : 5 ※ Ethernet/IP, CC-LINK/IE, MQTT는 추후, 추가될 예정입니다. . |
| DevCommSvr_IP | 서버 IP Address |
| DevCommSvr_Port | 서버 PORT 번호 |
| Username (option) | 서버와 연결하기 위해 필요한 User ID 입니다. 옵션입니다. User ID가 없으면 지정하지 않아도 됩니다. |
| Password (optional) | 서버와 연결하기 위해 필요한 PASS WORD 입니다. 옵션입니다. PASS WORD가 없으면 지정하지 않아도 됩니다. |
| exDllPath (optional) | 서버를 구동하기 위해 필요한 외부 Lib 경로 입니다. 각 프로토콜 별로 미리 지정된 lib가 있으므로 별도로 지정하지 않아도 됩니다. |

■ 비 가공장비 서버 리스트(산업용 통신 서버 리스트) 파일 저장 위치 작성한 파일은 " "Platform설치경로\Binary\ "에 저장하면 됩니다. ■ 주의 사항 TORUS Platform에서 산업용 통신 서버를 구동하고자 할 경우에는 반드시 DeviceCommSvrList.xml을 설정해야 합니다. 또한 각 App에서 서버의 데이터를 읽거나 쓰기 위해서는DeviceCommSvrList.xml 파일의 서버 속성 정보를 확인하고 설정 정보에 맞게 각 App의 mapping table 내용을 변경 해야 합니다. ( '3.1.5비 가공장비 어드레스 매핑 테이블 작성' 부분 참고) 

---

#### 3.1.5 비 가공장비 어드레스 매핑 테이블 작성 
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- 비가공장비 통신 어드레스 매핑 테이블 설정
TORUS Platform은 비가공장비의 데이터를 읽고 쓰거나 산업용 통신 서버의 데이터를 내부 Application이 읽고 쓸 수 있도록 하기 위해 별도의 가상 데이터 메모리를 가지고 있습니다. 비가공장비 및 산업용 통신 서버를 위한 데이터 모델 구조는 '6.1.1 비가공장비 데이터 모델의 구조' 를 참고하시기 바랍니다. TORUS Platform에 연결하는 각 비가공장비 Vendor 별로 네트워크로 접근할 수 있는 데이터의 주소와 데이터 타입, 데이터 명이 모두 다릅니다. 또한 산업용 통신 프로토콜에서 지원하는 데이터도 모두 다르기 때문에 이를 공용화하기 위해, 실제 비 가공장비 데이터 어드레스 및 산업용 통신 프로토콜 데이터 어드레스를 TORUS Platform의 가상 데이터 메모리의 어드레스에 매핑 시켜야 합니다. TORUS Platform을 이용하여 각 비가공장비에 접속하거나 플랫폼이 구동하는 산업용 통신 서버의 데이터를 읽고 쓰려고 할 때, 해당 기능을 사용하려는 App 마다 data mapping table을 정의해야 합니다. 이는 다양한 App들이 서로 동일한 Device에 접속하거나 동일한 서버의 데이터에 접근하더라도 서로 간의 간섭을 최소화 하기 위해서 입니다. ※ 하나의 Address mapping table을 만들고 여러 Application이 공유해도 됩니다. 다만, 이때에는 mapping table에 정의한 각 address들이 Application 간에 간섭이 발생하지 않도록 잘 정의해야 합니다.
- 비 가공장비 통신 어드레스 mapping table 속성 정보

비 가공장비 통신 어드레스용 mapping table의 구조는 다음 그림과 같습니다.

![image](./lib/NewItem484.png)
비 가공장비 통신 어드레스용 mapping table의 각 구성 요서에 대한 설명은 다음과 같습니다.

| Memory Block name | Memory Block type number |
| ----------------- | ------------------------ |
| rbitBlock | 1 |
| bitBlock | 2 |
| rbyteBlock | 3 |
| byteBlock | 4 |
| rwordBlock | 5 |
| wordBlock | 6 |
| rdwordBlock | 7 |
| dwordBlock | 8 |
| rqwordBlock | 9 |
| qwordBlock | 10 |

3. Data address 읽거나 지령할 장치의 값을 저장할 데이터의 주소를 의미합니다. 주소는 memory block 별로 독립되어 있기 때문에 같은 memory block 내에서만 유일한 값을 설정하면 됩니다. memory block이 다르면 같은 주소를 지정하더라도 문제가 없습니다. 4. Device ID TORUS Platform에 연결할 각 장치 또는 서버를 구분하는 ID 입니다. 이는 DeviceList.xml 혹은 DeviceCommSvrList.xml에 이미 정의된 값이어야 합니다. Device List 관련 내용은 ' 3.1.3 비 가공장비 클라이언트 리스트 작성' 부분 혹은 '3.1.4 비 가공장비 서버 리스트 작성' 부분을 참고 하시기 바랍니다. 5. Device Memory type Data address에 설정한 주소와 대응되는 장치 측 data address의 memory block type을 명시 합니다. 6. Target address Data address에 설정한 주소와 대응되는 장치 측 data address를 명시합니다. 7. Description 어떤 의미의 데이터인지 간단한 설명을 작성합니다. 반드시 입력해야 할 사항은 아닙니다.

| | |
| --- | --- |
| | |
| | |
| | |
| | |
| | |

- 비 가공장비 통신 어드레스용 mapping file

위 비 가공장비 통신 어드레스용 mapping table은 xml format으로 작성하며, 예제는 다음과 같습니다.

| <DataMaps> <DeviceData memory_ID="1" MemoryBlock="1" DataAddress="11" Device_ID="1" MemoryType="1" targetAddress="1" Description="Discrete-Input" /> <DeviceData memory_ID="1" MemoryBlock="2" DataAddress="12" Device_ID="1" MemoryType="2" targetAddress="1" Description="Coil"/> <DeviceData memory_ID="1" MemoryBlock="5" DataAddress="13" Device_ID="1" MemoryType="5" targetAddress="1" Description="Input-Register"/> <DeviceData memory_ID="1" MemoryBlock="6" DataAddress="14" Device_ID="1" MemoryType="6" targetAddress="1" Description="Holding-Register"/> </DataMaps> |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

위 비 가공장비 통신 어드레스용 mapping table에 정의된 내용은 다음과 같습니다. 2 line : MemoryBlock="1" 은 현재 정의하는 memory block이 read-only bit block type 임을 나타내며, 이 memory block의 어드레스 11번은 1번 장치(혹은 1번 서버)의 동일 type 어드레스 1번 데이터와 매핑된다는 의미 입니다. 5 line : MemoryBlock="6" 은 현재 정의하는 memory block이 word block type 임을 나타내며, 이 memory block의 어드레스 14번은 1번 장치(혹은 1번 서버)의 동일 type 어드레스 1번 데이터와 매핑된다는 의미 입니다. 비 가공장비 통신 어드레스용 mapping file에는 해당 mapping file을 사용하는 Application의 지원 기능에 따라 NC internal PLC 데이터에 대한 Address mapping 정보를 함께 구성할 수 있습니다. 이 경우에는 아래와 같은 형태가 됩니다

| <DataMaps> <InternalPlcData memory_ID="1" MemoryBlockType="6" DataAddress="1" Machine_ID="1" vendorCode="FANUC" DataType="1" targetAddress="D100" Description="FANUC-TEST1" /> <InternalPlcData memory_ID="1" MemoryBlockType="6" DataAddress="2" Machine_ID="1" vendorCode="FANUC" DataType="1" targetAddress="D101" Description="FANUC-TEST2" /> <InternalPlcData memory_ID="1" MemoryBlockType="6" DataAddress="3" Machine_ID="1" vendorCode="FANUC" DataType="1" targetAddress="D102" Description="FANUC-TEST3" /> <InternalPlcData memory_ID="1" MemoryBlockType="6" DataAddress="4" Machine_ID="1" vendorCode="FANUC" DataType="1" targetAddress="D103" Description="FANUC-TEST4" /> <InternalPlcData memory_ID="1" MemoryBlockType="8" DataAddress="100" Machine_ID="2" vendorCode="KCNC" DataType="2" targetAddress="PM0525" Description="KCNC-TEST1" /> <InternalPlcData memory_ID="1" MemoryBlockType="8" DataAddress="101" Machine_ID="2" vendorCode="KCNC" DataType="2" targetAddress="PM0526" Description="KCNC-TEST2" /> <InternalPlcData memory_ID="1" MemoryBlockType="8" DataAddress="102" Machine_ID="2" vendorCode="KCNC" DataType="2" targetAddress="PM0527" Description="KCNC-TEST3" /> <InternalPlcData memory_ID="1" MemoryBlockType="8" DataAddress="103" Machine_ID="2" vendorCode="KCNC" DataType="2" targetAddress="PM0528" Description="KCNC-TEST4" /> <DeviceData memory_ID="1" MemoryBlock="1" DataAddress="11" Device_ID="1" MemoryType="1" targetAddress="1" Description="Discrete-Input" /> <DeviceData memory_ID="1" MemoryBlock="2" DataAddress="12" Device_ID="1" MemoryType="2" targetAddress="1" Description="Coil"/> <DeviceData memory_ID="1" MemoryBlock="5" DataAddress="13" Device_ID="1" MemoryType="5" targetAddress="1" Description="Input-Register"/> <DeviceData memory_ID="1" MemoryBlock="6" DataAddress="14" Device_ID="1" MemoryType="6" targetAddress="1" Description="Holding-Register"/> </DataMaps> |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

위 mapping table의 내용은 xml file로 저장하면 됩니다. 저장위치는 해당 mapping file을 사용하는 Application과 동일한 위치 입니다. 비가공장비에 접근하거나 TORUS Platform이 구동하는 산업용 통신 서버의 데이터에 접근하려는 각 App은 개별 App 별도로 mapping table을 구성하고 이를 xml file로 저장한 후 initilaize 함수 호출 시, 3번째 파라메터에 해당 파일을 입력하여, TORUS Platform에 전달해야 합니다. 함수 호출과 관련된 사항은 " 7.2.1.1 Initialize "의 내용을 참고하시기 바랍니다. 

---

#### 3.1.6 NC internal PLC 어드레스 매핑 테이블 작성 
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

- NC internal PLC 어드레스 매핑 테이블 설정
TORUS Platform은 NC internal PLC의 데이터를 읽고 쓰기 위해 별도의 가상 데이터 메모리를 가지고 있습니다.

![image](./lib/NewItem%206.png)

![image](./lib/NewItem%207.png)

| | |
| --- | --- |

TORUS Platform에 연결하는 각 Vendor 별 CNC 마다 PLC 데이터의 주소와 데이터 타입, 데이터 명이 모두 다르므로 이를 공용화하기 위해, 실제 NC internal PLC 데이터 어드레스를 TORUS Platform의 PLC 가상 데이터 메모리의 어드레스에 매핑 시켜야 합니다. NC internal PLC 어드레스 매핑 테이블을 설정하는 것이 바로 NC 내부 PLC의 데이터 어드레스와 TORUS Platform의 PLC 가상 데이터 메모리 어드레스를 매핑시켜주는 일 입니다. TORUS Platform을 이용하여 NC 내부의 PLC(NC internal PLC) 데이터를 읽고 쓰고자 할 때에는 해당 기능을 사용하려는 App 마다 mapping table을 정의해야 합니다. 이는 다양한 App들이 서로 동일한 NC internal PLC Data에 접근하더라도 서로 간의 간섭을 최소화 하기 위해서 입니다. ※ 하나의 Address mapping table을 만들고 여러 Application이 공유해도 됩니다. 다만, 이때에는 mapping table에 정의한 각 address들이 Application 간에 간섭이 발생하지 않도록 잘 정의해야 합니다.
- NC internal PLC mapping table 속성 정보

NC internal PLC mapping table의 구조는 다음 그림과 같습니다. NC internal PLC 데이터 읽기/쓰기 기능을 사용하기 위해서는 이 기능을 사용하려는 App 마다, PLC Data Address mapping table을 구성하고 이를 file로 생성하여 TORUS Platform에 전달해야 합니다. PLC Data Address mapping table의 구성은 다음과 같습니다.

![image](./lib/NewItem%209.png)

| Memory Block name | Memory Block type number |
| ----------------- | ------------------------ |
| rbitBlock | 1 |
| bitBlock | 2 |
| rbyteBlock | 3 |
| byteBlock | 4 |
| rwordBlock | 5 |
| wordBlock | 6 |
| rdwordBlock | 7 |
| dwordBlock | 8 |
| rqwordBlock | 9 |
| qwordBlock | 10 |

각 memory block의 상세 설명은 '5.2.1.3 plc' 을 참고하십시오. 3. DataAddress 실제 NC internal PLC 데이터 어드레스와 mapping 시키기 위한 TORUS Platform의 가상 데이터 메모리 주소 입니다. 각 Memory Block 마다 1 ~ 65536 까지 할당 가능합니다. 4. Machine_ID 1~3번 필드까지 설정한 어드레스 정보가 어느 장비와 연결되는지 설정하는 항목 입니다. machineList.xml(혹은 machineList.aml) 파일에 정의한 machine ID를 참고하여 작성합니다. 5. VendorCode 연결하려는 장비에 어떤 CNC가 탑재되어 있는지 설정하는 항목 입니다. machineList.xml(혹은 machineList.aml) 파일에 정의한 "vendorcode" 값을 참고하여 작성합니다. 6. TargetDataType 바로 뒤에 설정할 TargetAddress가 실제 NC internal PLC에서는 어떤 데이터 타입인지 설정하는 항목 입니다. 설정할 PLC Target Address의 data type은 CNC Vendor 마다 각기 다른 부분들이 있기 때문에, 연결할 CNC Vendor를 확인 후 다음 표를 참고하여 작성하십시오

| CNC | Data type | 설정 값 | 설명 |
| ----------- | --------- | ------------------------ | -------------------- |
| FANUC | BYTE | 0 | 1 Byte 단위(8 bit) 데이터 |
| WORD | 1 | 16 bit 단위 데이터 | |
| LONG | 2 | 32 bit 단위 데이터 | |
| FLOATING 32 | 4 | 32 bit float(실수형) 단위 데이터 | |
| FLOATING 64 | 5 | 64 bit float(실수형) 단위 데이터 | |
| SIEMENS | BIT | 1 | 1 bit 단위 데이터 |
| BYTE | 2 | 1 Byte (8 bit) 단위 데이터 | |
| WORD | 4 | 16 bit 단위 데이터 | |
| DWORD | 8 | 32 bit 단위 데이터 | |
| KCNC TENUX | BIT | 0 | bit 단위 데이터 |
| LONG | 1 | 32 bit integer 단위 데이터 | |
| DOUBLE | 2 | 64 bit float(실수형) 단위 데이터 | |
| CSCAM | BIT | 0 | bit 단위 데이터 |
| LONG | 1 | 32 bit integer 단위 데이터 | |
| DOUBLE | 2 | 64 bit float(실수형) 단위 데이터 | |
| MITSUBISHI | BIT | 1 | 1 bit 단위 데이터 |
| BYTE | 8 | 1 Byte (8 bit) 단위 데이터 | |
| WORD | 16 | 16 bit 단위 데이터 | |
| DWORD | 32 | 32 bit 단위 데이터 | |

각 CNC 별로 위 표의 Data type에 해당하는 "설정 값"을 mapping table의 "TargetDataType" 항목의 값으로 설정하면 됩니다. 7. TargetAddress 실제로 읽고 쓰려는 NC internal PLC 데이터 어드레스를 설정하면 됩니다. TORUS Platform 가상 데이터 메모리 어드레스 하나에 원칙적으로 NC internal PLC에 있는 하나의 어드레스를 할당할 수 있기 때문에, TargetAddress에는 하나의 NC internal PLC 어드레스만 할당합니다. 그러나 FANUC의 경우에는 다음과 같이 할당할 수 있습니다. ex) TargetAddress = "D103-D104" 이때에는 BYTE TYPE D 어드레스 데이터를 두개를 묶어 하나의 TORUS Platform 가상 데이터 메모리 어드레스에 할당하는 것이므로 MemoryBlockType을 rbyteBlock이나 byteBlock으로 하면 안되고 byte type 2개를 합친 16 bit type인 rwordBlock이나 wordBlock으로 설정해야 합니다. 또한 TargetDataType도 BYTE TYPE으로 설정하면 안되고 WORD TYPE으로 설정해야 합니다. 아래 예제를 확인하십시오 <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="2" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D101" Description="FANUC-TEST2" /> <InternalPlcData Memory_ID="1" MemoryBlockType="6" DataAddress="4" Machine_ID="4" VendorCode="FANUC" TargetDataType="1" TargetAddress="D103-D104" Description="FANUC-TEST4" /> 8. Description 해당 어드레스에 대한 간략한 설명

| | | |
| --- | --- | --- |
| | | |
| | | |

위 설명한 바와 같이 mapping table을 구성한 후에 이를 아래와 같은 형태로 mapping file을 작성하여 App initialize 함수의 파라메터로 입력하면 됩니다.(3.3.2 절 참조)

| <DataMaps> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="1" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D100" Description="FANUC-TEST1" /> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="2" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D101" Description="FANUC-TEST2" /> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="3" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D102" Description="FANUC-TEST3" /> <InternalPlcData Memory_ID="1" MemoryBlockType="6" DataAddress="4" Machine_ID="4" VendorCode="FANUC" TargetDataType="1" TargetAddress="D103-D104" Description="FANUC-TEST4" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="100" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0525" Description="KCNC-TEST1" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="101" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0526" Description="KCNC-TEST2" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="102" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0527" Description="KCNC-TEST3" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="103" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0528" Description="KCNC-TEST4" /> <InternalPlcData Memory_ID="1" MemoryBlockType="6" DataAddress="11" Machine_ID="5" VendorCode="SIEMENS" TargetDataType="4" TargetAddress="DB10.DBW4" Description="SIEMENS-TEST1" /> </DataMaps> |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

mapping file에는 해당 mapping file을 사용하는 Application의 지원 기능에 따라 비가공장비 통신을 위한 Address mapping 정보를 함께 구성할 수 있습니다. 이 경우에는 아래와 같은 형태가 됩니다.

| <DataMaps> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="1" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D100" Description="FANUC-TEST1" /> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="2" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D101" Description="FANUC-TEST2" /> <InternalPlcData Memory_ID="1" MemoryBlockType="4" DataAddress="3" Machine_ID="4" VendorCode="FANUC" TargetDataType="0" TargetAddress="D102" Description="FANUC-TEST3" /> <InternalPlcData Memory_ID="1" MemoryBlockType="6" DataAddress="4" Machine_ID="4" VendorCode="FANUC" TargetDataType="1" TargetAddress="D103-D104" Description="FANUC-TEST4" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="100" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0525" Description="KCNC-TEST1" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="101" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0526" Description="KCNC-TEST2" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="102" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0527" Description="KCNC-TEST3" /> <InternalPlcData Memory_ID="1" MemoryBlockType="10" DataAddress="103" Machine_ID="1" VendorCode="KCNC" TargetDataType="2" TargetAddress="PM0528" Description="KCNC-TEST4" /> <InternalPlcData Memory_ID="1" MemoryBlockType="6" DataAddress="11" Machine_ID="5" VendorCode="SIEMENS" TargetDataType="4" TargetAddress="DB10.DBW4" Description="SIEMENS-TEST1" /> <DeviceData memory_ID="1" MemoryBlock="1" DataAddress="11" Device_ID="1" MemoryType="1" targetAddress="1" Description="Discrete-Input" /> <DeviceData memory_ID="1" MemoryBlock="2" DataAddress="12" Device_ID="1" MemoryType="2" targetAddress="1" Description="Coil"/> <DeviceData memory_ID="1" MemoryBlock="5" DataAddress="13" Device_ID="1" MemoryType="5" targetAddress="1" Description="Input-Register"/> <DeviceData memory_ID="1" MemoryBlock="6" DataAddress="14" Device_ID="1" MemoryType="6" targetAddress="1" Description="Holding-Register"/> </DataMaps> |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

위 mapping table의 내용은 xml file로 저장하면 됩니다. 저장위치는 해당 mapping file을 사용하는 Application과 동일한 위치 입니다. NC internal PLC 데이터에 접근하려는 각 App은 개별 App 별도로 mapping table을 구성하고 이를 xml file로 저장한 후 initilaize 함수 호출 시, 3번째 파라메터에 해당 파일을 입력하여, TORUS Platform에 전달해야 합니다. 함수 호출과 관련된 사항은 " 7.2.1.1 Initialize "의 내용을 참고하시기 바랍니다. 

---

#### 3.1.7 OPC UA 설정
3. TORUS Platform 설정과 실행/종료 3.1 플랫폼 설정 파일 작성 

■ 지멘스 OPC-UA 설정 플랫폼은 지멘스 대상 OPC-UA Server 에 대한 연결을 지원합니다. 연결 시 MachineList.xml에 설정한 Username, Password 속성을 사용하며, 접속 인증 파일을 "설치경로\ Binary\ OPC\pkiclient\{접속주소-IPAddress}\"에 생성합니다. OPC-UA 통신 연결 시, 기존 생성된 인증파일을 우선 사용하므로 비밀번호 변경이나 설비변경을 하고나서 OPC-UA Server에 접속이 되지 않는 경우 "설치경로\ Binary\ OPC\pkiclient\" 폴더를 삭제하여 기존 인증파일을 제거하고 재 접속하시기 바랍니다. 

---

### 3.2 플랫폼 실행과 종료
3. TORUS Platform 설정과 실행/종료 

TORUS Platform의 실행/종료는 다음과 같은 방법으로 수행합니다.
- 사전 준비
■ Application 준비 플랫폼 기반으로 구동할 Application을 “ 플랫폼실행폴더 ” 에 복사합니다. 또한 해당 Application의 등록정보 파일도 플랫폼실행폴더/application 폴더에 복사합니다. ※ 추후, 위 경로는 변경될 수도 있습니다. ■ TORUS Platform 설정 사항 확인 TORUS Platform 설정 사항이 정확히 작성되었는지 확인합니다. CNC가 탑재된 가공장비와 연결하기 위해서는 가공장비 리스트(machineList.xml)가 작성되어 있어야 합니다. '3.1.2 가공장비 리스트(MachineList) 작성' 을 참고하십시오. 비 가공장비와 연결하기 위해서는 비 가공장비 클라이언트 리스트를 작성해야 합니다. '3.1.3 비 가공장비 클라이언트 리스트 작성' 을 참고하십시오. 산업용 통신 프로토콜 서버를 운영하기 위해서는 비 가공장비 서버 리스트(산업용 통신 서버 리스트)를 작성해야 합니다. '3.1.4 비 가공장비 서버 리스트 작성' 을 참고하십시오. 비 가공장비 클라이언트 혹은 서버 기능을 사용하기 위해서는 address 매핑 테이블을 작성해야 합니다. '3.1.5 비 가공장비 어드레스 매핑 테이블 작성' 을 참고하십시오. 만약, 연결할 NC 내부 PLC 데이터를 읽고 쓸 예정이면, NC internal PLC 어드레스 매핑 테이블을 작성해야 합니다. '3.1.6 NC internal PLC 어드레스 매핑 테이블 작성' 을 참고하십시오. ■ NC 혹은 NC 시뮬레이터 실행 TORUS Platform을 구동하기 전에, 연결된 장비 혹은 NC 시뮬레이터에 전원이 인가되어 구동되고 있는 상태이거나 NC 애뮬레이터가 로컬 PC나 원격 PC 상에 구동되고 있는 상태이어야 합니다. TORUS Platform이 설치된 H/W와 NC가 네트워크로 연결되어 있는 경우, 플랫폼 구동 전에 네트워크 상태를 점검하는 것이 좋습니다 . TORUS Platform이 설치된 H/W와 NC 애뮬레이터가 원격으로 연결되어 있는 경우에도 사전에 네트워크 상태를 점검하는 것이 좋습니다. ■ 비 가공장치 실행 TORUS Platform을 구동하기 전에, 연결을 원하는 비 가공장비(로봇, PLC 및 가공장비 이외의 자동화 장비 등)들에 전원이 인가되어 구동되고 있는 상태이어야 합니다. TORUS Platform이 설치된 H/W와 비 가공장비가 네트워크로 연결되어 있을 경우, 플랫폼 구동 전에 네트워크 상태를 점검하는 것이 좋습니다.
- TORUS Platform 실행과 종료
■ 플랫폼 실행 TORUS Platform 구동을 위한 "Platform_run.bat" 배치 파일을 실행시키십시오. 배치 파일의 호출에 따라 mgrApplication.exe, mgrCommand.exe, mgrCommunication.exe 이 실행됩니다. mgrApplication.exe, mgrCommand.exe, mgrCommunication.exe 파일들을 직접 실행시켜도 무방합니다. 그 외, 다른 TORUS Platform manager 프로그램들은 구동을 원하는 프로그램 별로 수동으로 실행시키면 됩니다. ■ 플랫폼 종료 TORUS Platform 종료를 위한 "Platform_exit.bat"  배치 파일을 실행시키십시오. mgrApplication.exe, mgrCommand.exe, mgrCommunication.exe 이 종료됩니다. mgrApplication.exe, mgrCommand.exe, mgrCommunication.exe 파일들을 직접 종료하셔도 무방합니다. 임의로 실행시킨 다른 플랫폼 매니저 프로그램들은 수동으로 종료시켜야 합니다. 플랫폼 실행과 종료는 "플랫폼설치폴더\Doc\"에 있는 간편 사용법을 참고 하시기 바랍니다. 

---

## 4. TORUS Platform 기반 Application 개발 

TORUS Platform이 지원하는 기능을 사용하거나, Platform 기반의 Application을 탑재하기 위해 필요한 사항은 다음과 같습니다. 

---

### 4.1 Application 등록정보 파일
4. TORUS Platform 기반 Application 개발 

TORUS Platform 기반의 Application은 자신의 특성(고유한 속성) 정보를 Platform에 등록할 필요가 있습니다. 이를 위한 표준화된 형식을 “ Application 등록정보 파일 ” 로 규정하고 있습니다 . 

---

#### 4.1.1 Application 등록정보의 구성 속성들
4. TORUS Platform 기반 Application 개발 4.1 Application 등록정보 파일 

Application 등록정보 파일에 명시하여 플랫폼에 등록할 Application 등록정보의 구성 속성들은 다음의 <표 4>와 같습니다.

| 항목이름 | 내용 | 데이터 형 | 데이터 크기 | 형식 예 |
| -------------------- | -------------------------------------- | ------------ | ------ | -------------- |
| App name | Application의 이름, Application의 Label 역할 | string | 가변길이 | “tool Manager” |
| App Version | Application의 Version 정보 | string | 가변길이 | “1.1.0.1-T” |
| App File | Application 실행 파일의 full name (확장자 포함) | string | 가변길이 | “workApp.exe” |
| App Provider name | 외부에서 Application을 식별하는 유일한 이름 | string | 가변길이 | “tool_Mgr” |
| App ID | Application에 할당된 GUID | int | 가변길이 | “AC31C0F7-...” |
| App base group | Application이 속하는 Application-group 명시 | int | 32bit | 1 |
| App VIEW_ID | Application이 가지고 있는 화면(View)의 ID | List<string> | 가변길이 | 예시 참고 |
| FILTER | Application이 처리할 수 있는 데이터 정의 | List<string> | 가변길이 | 예시 참고 |
| App Backup file | 백업/복구가 필요한 파일 지정 (Full path) | bool | 가변길이 | 예시 참고 |
| Reboot after install | Application 설치 후 시스템 재 부팅 필요 여부 | bool | 32bit | TRUE/FALSE |
| Multiple Process | Application의 Multi Process 허용 여부 | bool | 32bit | TRUE/FALSE |
| Auto start | HMI System 부팅 후 자동 실행 여부 | bool | 32bit | TRUE/FALSE |
| Platform Version | Application을 설치.운용하기 위한 최소 플랫폼 버전 | string | 가변길이 | “1.1.1.1-rc” |

<표 4 - Application 등록정보 구성 속성표> 

---

#### 4.1.2 Application 등록정보 파일의 작성
4. TORUS Platform 기반 Application 개발 4.1 Application 등록정보 파일 

앞의 <표 4>에 나열한 각 속성 정보들을 설정하여 Platform에 등록하기 위해서는 각 Application 별로 “ Application 등록정보 파일 ” 에 작성해야 합니다.
- Application 등록정보 파일의 이름은 다음과 같이 지정합니다.
형식> Application실행파일명.info 예> workOffsetConf.exe 의 등록정보 파일은 “ workOffsetConf.info ” 로 지정
- Application 등록정보 파일에 속성 정보들을 작성할 때에는 json format에 따라 작성합니다.
아래의 예제를 참고하시기 바랍니다.

| { "App namel" : "Tool Manager", "App Version" : "1.1.0.1-t", "App File" : "workApp.exe", "App Provider name" : "toolManager.torus.co.kr", "App ID" : "XXXXXXXX", "App Base group" : 1, "App Pos_x" : 0, "App Pos_y" : 0, "App View_ID" : { "Tool_List" :{ "FILTER": [ "TOOL_LIST", "data://machine/tool/tool_list" ] }, "Tool_Set" :{ "FILTER" : [ "data://APP_WORK_OFFSET", "data://APP_PARAMETER" ] }, "Tool_Life" : { "FILTER": [ "data://APP_REGULAR_CHECK" ] }, "Tool_Monitor" : { "FILTER" : [ "data://APP_TOOL_MANAGER", "data://machine/channel/axisPos/", ] } }, "App Backup file" : [ "R:\\Source\\Json_Test\\AppManifestInfo.json", "R:\\Source\\Json_Test\\test_data.json" ], "Reboot after install" : false, "Multiple instance" : true, "Auto start" : false, "Platform Version" : "1.1.1.1-RC" } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

![image](./lib/NewItem468.png)
위 등록정보 파일 내용 중 주요 설정 항목에 대한 설명은 다음과 같습니다. ① App Provider name: 지능형 HMI에 탑재된 여러 Application 간에 데이터나 명령/이벤트를 교환할 때 상대 Application을 유일하게 식별할 수 있는 이름 입니다. 예시는 Application을 개발하고 제공하는 회사의 홈페이지 URL을 이용하여 “ App provider name ” 을 설정하였습니다. “ Application provider name ” 은 각 Application에 따라 다양한 형태로 설정할 수 있습니다. 단, “ / ” 문자가 포함되어서는 안되며, 다른 Application의 “ App provider name ” 과 중복되어서는 안됩니다. ② App ID: Intelligent HMI Platform이 지능형 HMI에 탑재된 Application을 유일하게 식별할 수 있는 ID 입니다. GUID를 생성하는 방법은 다음과 같습니다. “ Visual Studio의 메뉴 → 도구 → GUID 만들기 ” 에서 새로운 GUID를 생성할 수 있습니다. 이렇게 생성된 GUID는 해당 Application을 유일하게 식별할 수 있는 ID 값이 됩니다. GUID 생성 화면을 열면 다음의 <Fig 2>와 같은 화면이 나타납니다.

![image](./lib/NewItem30.png)
Fig 2 - GUID 만들기 위 <Fig 2> 화면에서 (5) 형식으로 GUID를 생성한 후, “” 속에 있는 ID 값을 속성 정보로 사용하면 됩니다. ③ App Base group: 해당 Application이 Application Group 중 어디에 속하는지 설정하는 등록정보 입니다. Application을 탑재할 HMI를 어떻게 구성하느냐에 따라 그 값이 달라지므로 HMI 구성 책임자에게 문의한 후 설정 값을 결정해야 합니다. ④ App VIEW-ID와 FILTER: 등록정보 예시 파일의 ④번 항목 내용은, 다른 Application으로부터 특정 데이터가 수신되었을 때 어떤 GUI 화면을 출력해야 하는지 지정하는 내용 입니다. (4-1)은 해당 Application의 화면 ID 입니다. Application의 GUI 화면 구성에 따라 한 개일 수도 있고 여러 개 일수도 있습니다. (4-2)는 데이터 필터 입니다. 각 VIEW-ID에 속한 FILTER에 정의된 데이터가 수신될 때, 해당 VIEW-ID에 해당하는 GUI 에서 이를 처리할 수 있다는 의미 입니다. 이 속성은 다른 Application으로부터 전송된 데이터 중에 수신을 허용하는 데이터(처리가 가능한 데이터)를 설정하는 것과 같은 의미를 지닙니다 . 예를 들어 test-view라는 VIEW-ID의 FILTER를 “ data://machine/channel/axis ” 라고 설정하면 NC의 모든 axis 관련 데이터가 수신되면 test-view에 해당하는 GUI 화면에서 이를 처리할 수 있다는 설정 내용이 됩니다. Application 등록정보 파일을 작성할 때, 등록정보 구성 속성을 모두 지정할 필요는 없습니다. 각 개별 Application 마다 필요한 부분만 정의하면 됩니다. 

---

### 4.2 Application 개발 시작하기
4. TORUS Platform 기반 Application 개발 

TORUS Platform은 소프트웨어 Application을 개발할 수 있도록 LIB를 제공합니다. Platform이 지원하는 LIB를 이용하여 Application을 개발하는 방법은 다음과 같습니다 . 

---

#### 4.2.1 새로운 프로젝트 생성
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 

TORUS Platform이 지원하는 Application 개발용 LIB는 Windows O.S에서 사용하도록 구성되어 있으며, 다음과 같은 사항을 참고하시기 바랍니다.
- 지원하는 프로그래밍 언어
- Microsoft C++/C#
- 지원하는 개발 툴
- Visual Studio 2012 이상, Visual Studio 2019 권장 (Visual Studio 2012보다 하위 버전에 대한 지원은 보장하지 않음) 

---

##### 4.2.1.1 C++ 프로젝트 생성
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 4.2.1 새로운 프로젝트 생성 

Platform의 Application 개발용 LIB를 이용하여 C++ 언어로 된 새로운 프로젝트를 생성하는 방법은 다음과 같습니다. "플랫폼 설치경로\Example_VS19" 폴더에 있는 예제 프로젝트들을 참고 하시기 바랍니다. (본 매뉴얼에서 소개하는 방법은 MFC Application Project를 기준으로 설명합니다) ① Microsoft Visual Studio를 이용하여 프로젝트 생성 시작 “ Visual Studio 실행 → 파일 → 새로 만들기 → 프로젝트 ” 로 프로젝트 생성 시작

![image](./lib/NewItem35.png)
② MFC 응용 프로그램 생성 MFC 응용 프로그램 선택 (본 매뉴얼에서는 Dialog 기반 MFC 응용 프로그램을 기준으로 설명함)

![image](./lib/NewItem36.png)
③ Platform LIB 복사 제공된 Platform LIB를 프로젝트 폴더 내 원하는 위치에 복사합니다. 특별한 설명이 없는 경우, Platform LIB는 “ Api ” 라는 이름의 폴더에 저장된 형태로 제공됩니다 . 본 매뉴얼에서는 “ $(SolutionDir)\ ” 에 복사하는 것으로 가정하고 설명을 진행합니다. 복사해야 할 Platform LIB는 다음과 같습니다. - intelligentApi.dll - intelligentApi.lib - intelligentApiCS.dll - ItemCS.dll - libAddress.dll - libAppInfo.dll - libCommandMaker.dll - libDatabase.lib - libExecuter.dll - libFocasIF.dll - libGuid.dll - libList.dll - libRpcClient.dll - libRpcServer.dll - libSharedMap.dll - libTrace.dll ④ 추가 포함 디렉터리 설정 “ 프로젝트 속성 → 구성속성 → C/C++ → 일반 ” 의 “ 추가 포함 디렉터리 ” 에 다음과 같이 추가합니다. “ $(SolutionDir)Api ”

![image](./lib/NewItem37.png)
⑤ 추가 라이브러리 디렉터리 설정 “ 프로젝트 속성 → 구성속성 → 링커 → 일반 ” 의 “ 추가 라이브러리 디렉터리 ” 에 다음과 같이 추가합니다. “ $(SolutionDir)Api ”

![image](./lib/NewItem38.png)
⑥ 추가 종속성 설정 “ 프로젝트 속성 → 구성속성 → 링커 → 입력 ” 의 “ 추가 종속성 ” 에 다음과 같이 추가합니다. “ intelligentApi.lib ”

![image](./lib/NewItem39.png)
⑦ Header 파일 추가 Platform LIB를 사용하기 위해, Source file에 다음과 같은 header file을 추가합니다.

| #include "Api.h" #include "item/document.h" #include "item/Writer.h" |
| -------------------------------------------------------------------- |

⑧ 프로젝트 build 및 실행 위 기술한 단계를 거치며 모든 설정을 완료하면, 기본적인 프로젝트 설정이 끝납니다. 이제 프로젝트를 빌드하고 실행할 수 있는 준비가 되었습니다. 

---

##### 4.2.1.2 C# 프로젝트 생성
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 4.2.1 새로운 프로젝트 생성 

Platform의 Application 개발용 LIB를 이용하여 C# 언어로 된 새로운 프로젝트를 생성하는 방법은 다음과 같습니다. "플랫폼 설치경로\Example_VS19" 폴더에 있는 예제 프로젝트들을 참고 하시기 바랍니다. (본 매뉴얼에서 소개하는 방법은 Winform Project를 기준으로 설명합니다) ① C# 응용 프로그램 생성 다음의 <Fig 11>와 같이, C# “ Windows Forms 응용 프로그램 ” 을 선택합니다 .

![image](./lib/NewItem40.png)
② Platform LIB 복사 제공된 Platform LIB를 프로젝트 폴더 내 원하는 위치에 복사합니다. 특별한 설명이 없는 경우, Platform LIB는 “ Api ” 라는 이름의 폴더에 저장된 형태로 제공됩니다 . 본 매뉴얼에서는 프로젝트의 솔루션 파일이 저장된 디렉터리[$(SolutionDir)\Api]에 복사하는 것으로 가정하고 설명을 진행합니다 . 복사해야 할 Platform LIB는 다음과 같습니다. - intelligentApi.dll - intelligentApi.lib - intelligentApiCS.dll - ItemCS.dll - libAddress.dll - libAppInfo.dll - libCommandMaker.dll - libDatabase.lib - libExecuter.dll - libFocasIF.dll - libGuid.dll - libList.dll - libRpcClient.dll - libRpcServer.dll - libSharedMap.dll - libTrace.dll ③ 참조 LIB 추가 “ 메뉴 → 프로젝트 → 참조추가 ” 선택 후, “ 찾아보기 ” 에서 직접 필요 라이브러리를 추가합니다. 추가해야 할 라이브러리는 다음과 같습니다. - ItemCS.dll - IntelligentApiCS.dll

![image](./lib/NewItem42.png)
참조할 라이브러리를 선택하면 다음의 <Fig 13>와 같이 추가할 참조 라이브러리가 목록에 나타납니다.

![image](./lib/NewItem43.png)
“ 확인 ” 을 눌러 라이브러리를 추가하면 됩니다. 참조할 라이브러리 추가가 성공하면 다음의 <Fig 14>와 같이 확인이 가능합니다.

![image](./lib/NewItem45.png)
④ namespace 적용 Platform에서 지원하는 LIB의 C#용 클래스들은 모두 다음의 namespace 에 정의되어 있습니다. “ IntelligentApiCS ” 위 명시된 namespace를 적용하기 위해 source code에 다음의 코드를 추가합니다.

| using IntelligentApiCS; |
| ----------------------- |

⑤ 프로젝트 빌드 및 실행 위 기술한 단계를 거치며 모든 설정을 완료하면, 기본적인 프로젝트 설정이 끝납니다. 이제 프로젝트를 빌드하고 실행할 준비가 되었습니다 . 

---

#### 4.2.2 Application에 Platform LIB 적용하기 
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 

TORUS Platform LIB를 적용하려는 Application이 Source File 내에 공통적으로 구성해야 할 코드 내용은 C++/C# 별로 다음과 같습니다 . 

---

##### 4.2.2.1 C++ Application 코드 구성
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 4.2.2 Application에 Platform LIB 적용하기 

C++ Application에 Platform LIB를 적용하기 위해 다음의 코드를 구성해야 합니다.
- Application name과 GUID 설정
현재 구현하는 Application의 Process를 생성하여 Platform에 등록하면서 함께 등록할 Application의 이름과 GUID를 설정해야 합니다. 예제 코드는 다음과 같습니다.

| const char* chAppGUID = "2E62F3EF-0A59-4948-BE46-00F862D723A7"; const char* AppName = "MFCApp"; |
| ----------------------------------------------------------------------------------------------- |

Application name 지정 시, 해당 Application등록정보 파일의 “ App Name ” 필드의 속성 값과 동일한 이름을 입력해야 합니다 .
- Platform LIB 객체 획득
Application에 Platform LIB를 적용하기 위해서는 Platform이 제공하는 LIB의 객체를 가져와야 합니다. 이때, 앞서 정의한 Application name과 GUID가 기본 Parameter로 사용됩니다. 만약 NC internal PLC 데이터를 사용하거나, 비가공장비 통신 기능을 사용한다면, 데이터 어드레스 Mapping file을 추가 Parameter로 사용해야 합니다. 예제 코드는 다음과 같습니다. 1> 비가공장비 통신 혹은 NC internal PLC 데이터 통신이 필요없는 경우

| CApi* m_api; m_api = CApi::Get(chAppGUID, "AppName"); |
| ----------------------------------------------------- |

2> 비가공장비 통신 혹은 NC internal PLC 데이터 통신 기능을 사용할 경우

| CApi* m_api; m_api = CApi::Get(chAppGUID, "AppName", "SampleAddrMapFile.xml"); |
| ------------------------------------------------------------------------------ |

비가공장비 통신 혹은 NC internal PLC 데이터 통신에 사용할 Mapping file의 구조는 "4.2.1.3 plc" 또는 "5. 비가공장비 데이터 모델"의 내용을 참고하면 됩니다.
- 필수 Callback 함수 등록
Life cycle에 따른 Application 상태 제어를 위해 Platform이 송신하는 event signal을 수신하여 처리하는 callback 함수를 정의해야 합니다. 어떤 Event signal에 대한 callback 함수를 정의할 것인지는 해당 Application의 동작 방식이나 특성에 따라 달라질 수 있습니다. 다음의 예제 코드는 “ OnEvent_Create”와 “ OnEvent_Show” Event signal에 대한 callback 입니다.

| static int OnCreate(int evt, int cmd, const char* command, char** result); static int OnShow(int evt, int cmd, const char* command, char** result); static int OnBroadcast(int evt, int cmd, const char* command, char** result); m_api = CApi::Get(chAppGUID, AppName); m_api->regist_callback(CALLBACK_ON_CREATE, &CWinixCppAppDlg::OnCreate ); m_api->regist_callback(CALLBACK_ON_SHOW, &CWinixCppAppDlg::OnShow); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- Application 초기화 코드 추가
위 코드가 구성되면 마지막으로 Application을 초기화 하는 코드를 구성하면 됩니다. Application 초기화는 플랫폼에 해당 Application을 최종적으로 사용 등록하는 역할을 담당합니다.

| m_api->initialize(); |
| -------------------- |

---

##### 4.2.2.2 C# Application 코드 구성
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 4.2.2 Application에 Platform LIB 적용하기 

C# Application에 Platform LIB를 적용하기 위해 다음의 코드를 구성해야 합니다 .
- Application name과 GUID 설정
현재 구현하는 Application의 Process를 생성하여 Platform에 등록하면서 함께 등록할 GUID를 설정해야 합니다. 예제 코드는 다음과 같습니다.

| Guid guid = new Guid("4300C7D2-FB9B-45B2-978C-DEB419FF5B94"); |
| ------------------------------------------------------------- |

- Application 초기화 코드 추가
위 코드가 구성되면 Application을 초기화 하는 코드를 구성하면 됩니다. Application 초기화는 플랫폼에 해당 Application을 최종적으로 사용 등록하는 역할을 담당합니다. Application 초기화를 위해 함수를 호출할 때, GUID와 Application name을 함께 입력하면 됩니다. Application name을 입력할 때에는 해당 Application 등록정보 파일의 “ App Name ” 필드의 속성 값과 동일한 이름을 입력해야 합니다. 만약 NC internal PLC 데이터를 사용하거나, 비가공장비 통신 기능을 사용한다면, 데이터 어드레스 Mapping file을 추가 Parameter로 사용해야 합니다. 예제 코드는 다음과 같습니다. 1> 비가공장비 통신 혹은 NC internal PLC 데이터 통신이 필요없는 경우

| Api.Initialize(guid, "Command Tester"); |
| --------------------------------------- |

2> 비가공장비 통신 혹은 NC internal PLC 데이터 통신 기능을 사용할 경우

| Api.Initialize(guid, "Command Tester", "SampleAddrMapFile.xml"); |
| ---------------------------------------------------------------- |

비가공장비 통신 혹은 NC internal PLC 데이터 통신에 사용할 Mapping file의 구조는 "4.2.1.3 plc" 또는 "5. 비가공장비 데이터 모델"의 내용을 참고하면 됩니다.
- 필수 Callback 함수 등록
Life cycle에 따른 Application 상태 제어를 위해 Platform이 송신하는 event signal을 수신하여 처리하는 callback 함수를 정의해야 합니다. 어떤 Event signal에 대한 callback 함수를 정의할 것인지는 해당 Application의 동작 방식이나 특성에 따라 달라질 수 있습니다. 다음의 예제 코드는 “ OnEvent_Create”와 “ OnEvent_Show” “ OnEvent_Run ” Event signal에 대한 callback 입니다.

| Api.OnEvent_Create += Api_OnEvent_Create; Api.OnEvent_Show += Api_OnEvent_Show; Api.OnEvent_Run += Api_OnEvent_Run; void Api_OnEvent_Show(ApiEventArgs e) {…} void Api_OnEvent_Run(ApiEventArgs e) {…} void Api_OnEvent_Create(ApiEventArgs e) {…} |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#으로 Application을 개발할 경우, Event signal에 대한 Callback 함수 등록 방법이 하나 더 있습니다. 예제 코드는 다음과 같습니다 .

| Api.regist_callback(CALLBACK_TYPE.ON_CREATE, OnCreate); Api.regist_callback(CALLBACK_TYPE.ON_SHOW, OnShow); Api.regist_callback(CALLBACK_TYPE.ON_RUN, OnRun); static int OnCreate(EVENT_CODE evt, int cmd, Item command, ref Item result) {…} static int OnShow(EVENT_CODE evt, int cmd, Item command, ref Item result) {…} static int OnRun(EVENT_CODE evt, int cmd, Item command, ref Item result) {…} |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

Callback 함수 구현에 대한 상세한 사항은 5.2.6.4와 5.2.6.5를 참고하면 됩니다 . 

---

#### 4.2.3 Application테스트/디버깅
4. TORUS Platform 기반 Application 개발 4.2 Application 개발 시작하기 

실제 NC 연결 없이, 사용자의 개발용 PC에서 테스트/디버깅 할 때에는 다음의 내용을 참고 하십시오

| 순서 | 구분 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| --- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| ① | NC 애뮬레이터 실행 | FANUC NC GUIDE를 실행합니다. NC GUIDE의 상세한 사용방법은 FANUC 홈페이지 혹은 NC GUIDE 사용자 매뉴얼을 참고하시기 바랍니다. | SIEMENS Sinutrain을 실행시킵니다. Sinutrain의 자세한 사용 방법은 SIEMENS 홈페이지 혹은 Sinutrain 사용자 설명서를 참조하시기 바랍니다. | CSCAM NC Emulator를 실행합니다. CSCAM NC Emulator의 상세한 사용 방법은 CSCAM 홈페이지 혹은 CSCAM NC Emulator 사용자 매뉴얼을 참고 하시기 바랍니다. | MITSUBISHI NC Trainer2를 실행합니다. NC Trainer2의 상세한 사용방법은 MITSUBISHI 홈페이지 혹은 NC Trainer2 사용자 매뉴얼을 참고하시기 바랍니다. | KCNC의 TENUX Emulator를 실행합니다. TENUX Emulator의 상세한 사용 방법은 KCNC 홈페이지 혹은 TENUX Emulator 사용자 매뉴얼을 참고하시기 바랍니다. |
| ② | Platform 실행 | Platform 구동과 종료를 위한 batch file (Platform_run.bat, Platform_exit.bat)을 실행시킵니다. Platform이 구동되면, Application manager, Communication Manager, Command Manager, Log Manager가 동작합니다. 플랫폼 설정에 따라 콘솔 창으로 화면에 표시될 수도 있습니다. | | | | |
| ③ | Application실행 | 이제 Application을 실행하면서 테스트를 진행하면 됩니다. Application의 디버깅 작업은 Visual Studio Debugging mode에서 Application을 실행시킨 후 Visual Studio의 디버깅 기능을 이용하면 됩니다. Visual Studio의 디버깅 기능은 Visual Studio 매뉴얼을 참고하시기 바랍니다. | | | | |

---

## 5. CNC 공통 데이터 모델

TORUS Platform 에서는 CNC 공통 데이터 모델을 "Machine Data Model" 이라고 합니다. 

---

### 5.1 Machine Data Model 정의
5. CNC 공통 데이터 모델 

Machine Data Model은 이종 벤더 CNC의 데이터 중 공통된 데이터들을 추출하여 공용화 하고 이를 이용해 공작기계의 물리 구조와 상태를 가상화하도록 구성한 데이터 모델입니다. 

---

#### 5.1.1 Machine Data Model의 구조
5. CNC 공통 데이터 모델 5.1 Machine Data Model 정의 

Machine Data Model 의 구조는 다음의 <표 6>과 같은 계층 구조로 되어 있습니다.

| machine [ ] | cncModel | | | | |
| ---------------------------------- | ----------------------- | ------------------ | --- | --- | --- |
| numberOfChannels | | | | | |
| cncVendor | | | | | |
| ncLinkState | | | | | |
| currentAccessLevel | | | | | |
| basicLengthUnit | | | | | |
| machinePowerOnTime | | | | | |
| currentCncTime | | | | | |
| machineType | | | | | |
| ncMemory | totalCapacity | | | | |
| usedCapacity | | | | | |
| freeCapacity | | | | | |
| rootPath | | | | | |
| channel [ ] | channelEnabled | | | | |
| toolAreaNumber | | | | | |
| numberOfAxes | | | | | |
| numberOfSpindles | | | | | |
| alarmStatus | | | | | |
| numberOfAlarms | | | | | |
| operateMode | | | | | |
| numberOfWorkOffsets | | | | | |
| ncState | | | | | |
| motionStatus | | | | | |
| emergencyStatus | | | | | |
| axis [ ] | machinePosition | | | | |
| workPosition | | | | | |
| distanceToGo | | | | | |
| relativePosition | | | | | |
| axisName | | | | | |
| relativeAxisName | | | | | |
| axisLoad | | | | | |
| axisFeed | | | | | |
| axisLimitPlus | | | | | |
| axisLimitMinus | | | | | |
| workAreaLimitPlus | | | | | |
| workAreaLimitMinus | | | | | |
| workAreaLimitPlusEnabled | | | | | |
| workAreaLimitMinusEnabled | | | | | |
| axisEnabled | | | | | |
| interlockEnabled | | | | | |
| constantSurfaceSpeedControlEnabled | | | | | |
| axisCurrent | | | | | |
| machineOrigin | | | | | |
| axisTemperature | | | | | |
| axisPower | actualPowerConsumption | | | | |
| powerConsumption | | | | | |
| regeneratedPower | | | | | |
| spindle [ ] | spindleLoad | | | | |
| spindleOverride | | | | | |
| spindleLimit | | | | | |
| spindleEnabled | | | | | |
| spindleCurrent | | | | | |
| spindleTemperature | | | | | |
| rpm | commandedSpeed | | | | |
| actualSpeed | | | | | |
| speedUnit | | | | | |
| spindlePower | actualPowerConsumption | | | | |
| powerConsumption | | | | | |
| regeneratedPower | | | | | |
| feed | feedOverride | | | | |
| rapidOverride | | | | | |
| feedRate | commandedSpeed | | | | |
| actualSpeed | | | | | |
| speedUnit | | | | | |
| workStatus [ ] | workCounter | currentWorkCounter | | | |
| targetWorkCounter | | | | | |
| totalWorkCounter | | | | | |
| machiningTime | processingMachiningTime | | | | |
| estimatedMachiningTime | | | | | |
| machineOperationTime | | | | | |
| actualCuttingTime | | | | | |
| activeTool | locationNumber | | | | |
| toolName | | | | | |
| toolNumber | | | | | |
| numberOfEdges | | | | | |
| toolEnabled | | | | | |
| magazineNumber | | | | | |
| sisterToolNumber | | | | | |
| toolLifeUnit | | | | | |
| toolGroupNumber | | | | | |
| toolUseOrderNumber | | | | | |
| toolStatus | | | | | |
| toolEdge | edgeNumber | | | | |
| toolType | | | | | |
| lengthOffsetNumber | | | | | |
| geoLengthOffset | | | | | |
| wearLengthOffset | | | | | |
| radiusOffsetNumber | | | | | |
| geoRadiusOffset | | | | | |
| wearRadiusOffset | | | | | |
| edgeEnabled | | | | | |
| geoLengthOffsetZ | | | | | |
| wearLengthOffsetZ | | | | | |
| geoLengthOffsetY | | | | | |
| wearLengthOffsetY | | | | | |
| geoOffsetNumber | | | | | |
| wearOffsetNumber | | | | | |
| cuttingEdgePosition | | | | | |
| tipAngle | | | | | |
| holderAngle | | | | | |
| insertAngle | | | | | |
| insertWidth | | | | | |
| insertLength | | | | | |
| referenceDirectionHolderAngle | | | | | |
| directionOfSpindleRotation | | | | | |
| numberOfTeeth | | | | | |
| toolLife | maxToolLife | | | | |
| restToolLife | | | | | |
| toolLifeCount | | | | | |
| toolLifeAlarm | | | | | |
| currentProgram | sequenceNumber | | | | |
| currentBlockCounter | | | | | |
| lastBlock | | | | | |
| currentBlock | | | | | |
| nextBlock | | | | | |
| activePartProgram | | | | | |
| programMode | | | | | |
| currentWorkOffsetIndex | | | | | |
| currentWorkOffsetCode | | | | | |
| currentDepthLevel | | | | | |
| modal [ ] | modalIndex | | | | |
| modalCode | | | | | |
| overallBlock [ ] | blolckCounter | | | | |
| programName | | | | | |
| interruptBlock [ ] | depthLevel | | | | |
| blockCounter | | | | | |
| programName | | | | | |
| blockData | | | | | |
| searchType | | | | | |
| mainProgramName | | | | | |
| currentTotalWorkOffset | workOffsetIndex | | | | |
| workOffsetCode | | | | | |
| workOffsetValue [ ] | | | | | |
| workOffsetRotation [ ] | | | | | |
| workOffsetScalingFactor [ ] | | | | | |
| workOffsetMirroringEnabled [ ] | | | | | |
| currentFile | programName | | | | |
| programPath | | | | | |
| programSize | | | | | |
| programDate | | | | | |
| programNameWithPath | | | | | |
| mainFile | programName | | | | |
| programPath | | | | | |
| programSize | | | | | |
| programDate | | | | | |
| programNameWithPath | | | | | |
| controlOption | singleBlock | | | | |
| dryRun | | | | | |
| optionalStop | | | | | |
| blockSkip [ ] | | | | | |
| machineLock | | | | | |
| workOffset [ ] | workOffsetValue [ ] | | | | |
| workOffsetRotation [ ] | | | | | |
| workOffsetScalingFactor [ ] | | | | | |
| workOffsetMirroringEnabled [ ] | | | | | |
| workOffsetFine [ ] | | | | | |
| alarm [ ] | alarmText | | | | |
| alarmCategory | | | | | |
| alarmNumber | | | | | |
| raisedTimeStamp | | | | | |
| variable [ ] | userVariable | | | | |
| plc | memory | rbitBlock [ ] | | | |
| bitBlock [ ] | | | | | |
| rbyteBlock [ ] | | | | | |
| byteBlock [ ] | | | | | |
| rwordBlock [ ] | | | | | |
| wordBlock [ ] | | | | | |
| rdwordBlock [ ] | | | | | |
| dwordBlock [ ] | | | | | |
| rqwordBlock [ ] | | | | | |
| qwordBlock [ ] | | | | | |
| toolArea [ ] | toolAreaEnabled | | | | |
| numberOfMagazines | | | | | |
| numberOfRegisteredTools | | | | | |
| numberOfLoadedTools | | | | | |
| numberOfToolGroups | | | | | |
| numberOfToolOffsets | | | | | |
| magazine [ ] | magazineEnabled | | | | |
| magazineName | | | | | |
| numberOfRealLocations | | | | | |
| magazinePhysicalNumber | | | | | |
| numberOfLoadedTools | | | | | |
| tools [ ] | locationNumber | | | | |
| toolName | | | | | |
| numberOfEdges | | | | | |
| toolEnabled | | | | | |
| magazineNumber | | | | | |
| sisterToolNumber | | | | | |
| toolLifeUnit | | | | | |
| toolGroupNumber | | | | | |
| toolUseOrderNumber | | | | | |
| toolStatus | | | | | |
| toolEdge [ ] | toolType | | | | |
| lengthOffsetNumber | | | | | |
| geoLengthOffset | | | | | |
| wearLengthOffset | | | | | |
| radiusOffsetNumber | | | | | |
| geoRadiusOffset | | | | | |
| wearRadiusOffset | | | | | |
| edgeEnabled | | | | | |
| geoLengthOffsetZ | | | | | |
| wearLengthOffsetZ | | | | | |
| geoLengthOffsetY | | | | | |
| wearLengthOffsetY | | | | | |
| geoOffsetNumber | | | | | |
| wearOffsetNumber | | | | | |
| cuttingEdgePosition | | | | | |
| tipAngle | | | | | |
| holderAngle | | | | | |
| insertAngle | | | | | |
| insertWidth | | | | | |
| insertLength | | | | | |
| referenceDirectionHolderAngle | | | | | |
| directionOfSpindleRotation | | | | | |
| numberOfTeeth | | | | | |
| toolLife | maxToolLife | | | | |
| restToolLife | | | | | |
| toolLifeCount | | | | | |
| toolLifeAlarm | | | | | |
| registerTools [ ] | locationNumber | | | | |
| toolName | | | | | |
| numberOfEdges | | | | | |
| toolEnabled | | | | | |
| magazineNumber | | | | | |
| sisterToolNumber | | | | | |
| toolLifeUnit | | | | | |
| toolGroupNumber | | | | | |
| toolUseOrderNumber | | | | | |
| toolStatus | | | | | |
| toolEdge [ ] | toolType | | | | |
| lengthOffsetNumber | | | | | |
| geoLengthOffset | | | | | |
| wearLengthOffset | | | | | |
| radiusOffsetNumber | | | | | |
| geoRadiusOffset | | | | | |
| wearRadiusOffset | | | | | |
| edgeEnabled | | | | | |
| geoLengthOffsetZ | | | | | |
| wearLengthOffsetZ | | | | | |
| geoLengthOffsetY | | | | | |
| wearLengthOffsetY | | | | | |
| geoOffsetNumber | | | | | |
| wearOffsetNumber | | | | | |
| cuttingEdgePosition | | | | | |
| tipAngle | | | | | |
| holderAngle | | | | | |
| insertAngle | | | | | |
| insertWidth | | | | | |
| insertLength | | | | | |
| referenceDirectionHolderAngle | | | | | |
| directionOfSpindleRotation | | | | | |
| numberOfTeeth | | | | | |
| toolLife | maxToolLife | | | | |
| restToolLife | | | | | |
| toolLifeCount | | | | | |
| toolLifeAlarm | | | | | |
| buffer [ ] | bufferEnabled | | | | |
| numberOfStream | | | | | |
| statusOfStream | | | | | |
| modOfStream | | | | | |
| machineChannelOfStream | | | | | |
| periodOfStream | | | | | |
| triggerOfStream | | | | | |
| frequencyOfStream | | | | | |
| stream [ ] | streamEnabled | | | | |
| streamFrequency | | | | | |
| streamCategory | | | | | |
| streamSubcategory | | | | | |
| streamType | | | | | |
| streamStartBit | | | | | |
| streamEndBit | | | | | |
| value | | | | | |

<표 6 - Machine Data Model 계층 구조> 

---

### 5.2 데이터 모델의 각 데이터 설명
5. CNC 공통 데이터 모델 

TORUS 이 지원하는 Machine Data Model의 각 데이터 별 상세 설명은 다음과 같습니다. 

---

#### 5.2.1 machine
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 

- 개요 machine 데이터는 단위 공작기계를 식별하고 해당 장비에 대한 상태 정보를 나타내며, 기본적인 장비 구성 정보와 함께 사용 가능한 계통, 보유 프로그램 리스트, 보유 공구 리스트 등을 포함합니다.

- 데이터 구성

| machine | | |
| ------------------ | --------------------------- | ---------- |
| cncModel | : STRING, | Read-only; |
| numberOfChannels | : INTEGER, | Read-only; |
| cncVendor | : INTEGER, | Read-only; |
| ncLinkState | : BOOLEAN, | Read-only; |
| currentAccessLevel | : INTEGER, | Read-only; |
| basicLengthUnit | : INTEGER, | Read-only; |
| machinePowerOnTime | : REAL, | Read-only; |
| currentCncTime | : STRING, | Read-only; |
| machineType | : INTEGER, | Read-only; |
| ncMemory | : ncMemory; | |
| channel | : LIST [1:N] OF “channel”; | |
| plc | : plc | |
| toolArea | : LIST [1:N] OF “toolArea”; | |
| buffer | : LIST [1:N] OF "buffer" | |

- 구성 데이터 설명

- cncModel 해당 장비에 탑재된 NC의 모델명을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/cncModel?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- numberOfChannels 해당 장비에서 사용 가능한 계통의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/numberOfChannels?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- cncVendor 해당 장비에 탑재된 NC의 NC 메이커를 나타내며, 각 NC 제조사에 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/cncVendor?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.

| 결과 |
| -------------- |
| 1 : FANUC |
| 2 : SIEMENS |
| 3 : CSCAM |
| 4 : MITSUBISHI |
| 5 : KCNC |

- ncLinkState 해당 장비에 탑재된 NC와의 통신 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/ncLinkState?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- currentAccessLevel (SIEMENS only) 해당 장비에서 프로그램 또는 디렉토리 실행, 쓰기, 나열 및 읽기에 대한 사용 권한을 나타냅니다. 사용 권한의 7단계 보안 수준을 표현하며, 1단계가 가장 높은 수준, 7단계가 가장 낮은 수준입니다. 각 사용 권한에 대응하는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/currentAccessLevel?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.

| SIEMENS |
| ---------------------- |
| 1 : 제조자 |
| 2 : 서비스 |
| 3 : 사용자 |
| 4 : 프로그래머 (키 스위치 3) |
| 5 : 공인 전문가 ( 키 스위치 2) |
| 6 : 숙련된 전문가 (키 스위치 1) |
| 7 : 준 숙련 전문가 (키 스위치 0) |

- basicLengthUnit 해당 장비에서 사용하는 길이 값들의 단위를 나타내며, 각 NC 에서 이용가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/basicLengthUnit?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| --------------- | ----- | ------- | ----- | ---------- | ---- |
| 0: metrics | O | O | O | O | O |
| 1: inches | O | O | O | O | O |
| 4 : user Define | | O | | | |

- machinePowerOnTime 해당 장비의 전원이 켜진 시간을 나타내는 실수형 속성입니다. (단위 : 분)

주소 표기는 다음과 같이 합니다. data://machine/machinePowerOnTime?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- currentCncTime 해당 장비에 설정되어 있는 현재시각을 나타내는 문자열 속성입니다. (형식 : yyyy-MM-ddTHH:mm:ss)

주소 표기는 다음과 같이 합니다. data://machine/currentCncTime?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- machineType 해당 장비의 타입을 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/machineType?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.

| 결과 |
| ----------- |
| 0 : 알수없음 |
| 1 : milling |
| 2 : lathe |

- ncMemory 해당 장비의 NC 메모리 용량을 나타내는 데이터로 ncMemory 타입으로 정의됩니다.

자세한 설명은 " 5.2.1.1 ncMemory " 절에서 확인할 수 있습니다.
- channel 해당 장비에서 사용 가능한 계통을 나타내며, channel 타입으로 정의됩니다. 기본적으로는 하나의 계통을 가지나 다계통 장비의 경우 복수개의 계통을 리스트로 할당할 수 있습니다. "Filter" 로 channel 을 사용하여 리스트 내 개체를 식별합니다. (예: channel=1) 자세한 설명은 " 5 .2.1.2 channel " 절에서 확인할 수 있습니다.
- plc 이기종 CNC 내부 PLC (NC internal PLC)의 데이터를 나타내며, plc 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.3 plc " 절에서 확인할 수 있습니다.
- toolArea 해당 장비에서 사용 가능한 공구 영역의 리스트를 나타내며, 각 공구 영역은 toolArea 타입으로 정의됩니다. 화낙과 CSCAM에는 해당 속성과 대응되는 데이터가 존재하지 않으므로 디폴트로 1이 설정됩니다.  "Filter" 로 toolArea 을 사용하여 리스트 내 개체를 식별합니다. (예: toolArea=1) 자세한 설명은 " 5 .2.1.4 toolArea " 절에서 확인할 수 있습니다.
- buffer CNC 구동계에 내장된 센서 데이터 수집에 대한 정보를 나타내며, buffer의 stream별로 센서 데이터를 수집합니다. KCNC와 FANUC NC 대상으로만 지원하는 기능입니다. "Filter"로 buffer를 사용하여 리스트 내 개체를 식별합니다. (얘: buffer=1) 자세한 설명은 " 5 .2.1.5 buffer " 절에서 확인할 수 있습니다.

---

##### 5.2.1.1 ncMemory
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 

- 개요 ncMemory 데이터는 공작기계의 NC 메모리 용량에 관한 정보를 나타내며, 전체 용량, 사용 용량, 잔여 용량 등을 포함합니다.

- 데이터 구성

| ncMemory | | |
| ------------- | --------- | ---------- |
| totalCapacity | : REAL, | Read-only; |
| userCapacity | : REAL, | Read-only; |
| freeCapacity | : REAL, | Read-only; |
| rootPath | : STRING, | Read-only; |

- 구성 데이터 설명

- totalCapacity NC 메모리의 전체 용량을 나타내는 실수형 속성입니다. (단위 : byte)

주소 표기는 다음과 같이 합니다. data://machine/ncMemory/totalCapacity?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- usedCapacity NC 메모리의 사용 중인 용량을 나타내는 실수형 속성입니다. (단위 : byte)

주소 표기는 다음과 같이 합니다. data://machine/ncMemory/usedCapacity?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- freeCapacity NC 메모리의 잔여 용량을 나타내는 실수형 속성입니다. (단위 : byte)

주소 표기는 다음과 같이 합니다. data://machine/ncMemory/freeCapacity?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다.
- rootPath NC 메모리의 기본 경로를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/ncMemory/rootPath?machine=i i 는 몇 번째 장비인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2 channel
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 

- 개요 channel 데이터는 계통 별로 기록되는 상태 정보를 나타내며, 계통의 식별자 정보와 함께 제어 가능한 축 정보, 연결된 스핀들 정보, 이송 상태 정보, 작업 상태 정보, 활성화된 공구 정보, 실행 중인 프로그램 정보 등을 포함합니다. 다만, 지멘스의 경우 화낙과 다르게 축 개념에 스핀들을 포함합니다.

- 데이터 구성

| channel | | |
| ------------------- | ----------------------------- | ---------- |
| channelEnabled | : BOOLEAN, | Read-only; |
| toolAreaNumber | : INTEGER, | Read-only; |
| numberOfAxes | : INTEGER, | Read-only; |
| numberOfSpindles | : INTEGER, | Read-only; |
| alarmStatus | : INTEGER, | Read-only; |
| numberOfAlarms | : INTEGER, | Read-only; |
| operateMode | : INTEGER, | Read-only; |
| numberOfWorkOffsets | : INTEGER, | Read-only; |
| ncState | : INTEGER, | Read-only; |
| motionStatus | : INTEGER, | Read-only; |
| emergencyStatus | : INTEGER, | Read-only; |
| axis | : LIST [1:N] OF “axis”; | |
| spindle | : LIST [1:N] OF “spindle”; | |
| feed | : feed; | |
| workStatus | : LIST [1:N] OF “workStatus”; | |
| activeTool | : activeTool; | |
| currentProgram | : currentProgram; | |
| workOffset | : LIST [1:N] OF “workOffset”; | |
| alarm | : LIST [1:N] OF “alarm”; | |
| variable | : LIST [1:N] OF “variable”; | |

- 구성 데이터 설명

- channelEnabled 해당 계통의 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/channelEnabled?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- toolAreaNumber 해당 계통에서 사용 가능한 공구 영역의 식별 번호를 나타내는 정수형 속성입니다. 단계통 장비의 경우 디폴트로 1이 세팅될 수 있습니다. FANUC에서는 공구 영역과 계통이 동일하기 때문에 channel과 toolArea가 같은 개념으로 사용됩니다. SIEMENS의 공구 영역의 개수는 계통 수와 동등하며, 공구 영역과 계통 간 1:다 관계가 성립합니다. 하나의 공구 영역은 여러 개의 계통에 의해 참조될 수 있지만, 하나의 계통이 여러 개의 공구 영역을 참조하는 것은 불가능합니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/toolAreaNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- numberOfAxes 해당 계통에서 사용 가능한 축의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/numberOfAxes?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- numberOfSpindles 해당 계통에서 사용 가능한 스핀들의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/numberOfSpindles?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- alarmStatus 해당 계통에서 발생한 알람의 상태 정보를 나타내며, 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarmStatus?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ---------------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : no alarm | O | O | O | O | O |
| 1 : alarm | O | | O | O | O |
| 2 : alarm without stop | | O | | | |
| 3 : alarm with stop | | O | | | |
| 4 : Battery low | O | | | | |
| 5 : FAN | O | | | | |
| 6 : PS Warning | O | | | | |
| 7 : FSSB warning | O | | | | |
| 8 : Insulate warning | O | | | | |
| 9 : Encoder warning | O | | | | |
| 10 : PMC alarm | O | | | | |

- numberOfAlarms 해당 계통에서 발생한 알람의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/numberOfAlarms?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- operateMode 공작기계의 운전 모드를 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/operateMode?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| --------------------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : JOG | O | O | O | O | O |
| 1 : MDI | O | O | O | O | O |
| 2 : MEMORY(AUTO) | O | O | O | O | O |
| 3 : ZRN | | | O | | O |
| 4 : MPG | | | O | | O |
| 5 : **** | O | | O | | O |
| 6 : EDIT | O | | O | | O |
| 7 : HANDLE | O | | | O | |
| 8 : Teach in JOG | O | | | | |
| 9 : Teach in HANDLE | O | | | | |
| 10 : INC·feed | O | | | | |
| 11 : REFERENCE | O | | | O | |
| 12 : REMOTE | O | | | | |
| 13 : JOG-REPOS | | O | | | |
| 14 : MDI-REF.POINT | | O | | | |
| 15 : MDI-TEACH IN | | O | | | |
| 16 : MDI-TECH IN-REF.POINT | | O | | | |
| 17 : AUTO-TECH IN-REF.POINT | | O | | | |
| 18 : STEP | | | O | O | O |
| 19 : RAPID | | | | O | |
| 20 : TAPE | | | | O | |
| 21 : AUTO-TEACH IN-JOG | | O | | | |
| 22 : JOG-REF | | O | | | |

- numberOfWorkOffsets 공작기계의 작업물 좌표계 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/numberOfWorkOffsets?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- ncState CNC의 작동 상태를 나타내며, 각 NC 에서 이용가능한 값들과 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/ncState?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| -------------------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : **** (=reset) | O | O | O | O | O |
| 1 : Stop | O | | O | O | O |
| 2 : Hold | O | | O | | O |
| 3 : Start (=Active) (=Run) | O | O | O | O | O |
| 4 : MSTR | O | | | | |
| 5 : Interrupted | | O | | | |
| 6 : Pause | | | | O | |

- motionStatus 장비의 현재 Motion, Dwell 상태 여부를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/motionStatus?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ---------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : *** | O | | O | | O |
| 1 : Motion | O | O | O | O | O |
| 2 : Dwell | O | O | O | O | O |
| 3 : Wait | O | | | | |

- emergencyStatus 장비가 현재 emergency상태인지 여부를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/emergencyStatus?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ----------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : Not emergency | O | O | O | | O |
| 1 : Emergency | O | O | O | | O |
| 2 : Reset | O | | | | |
| 3 : Wait | O | | | | |

- axis axis는 해당 계통에서 제어할 수 있는 축의 리스트를 나타내며, 각 축은 axis 타입으로 정의됩니다. "Filter" 로 axis 을 사용하여 리스트 내 개체를 식별합니다. (예: axis=1) 자세한 설명은 " 5.2.1.2.1 axis " 절에서 확인할 수 있습니다.

- spindle 해당 계통에 연결되어 있는 스핀들의 리스트를 나타내며, 각 스핀들은 spindle 타입으로 정의됩니다. "Filter" 로 spindle 을 사용하여 리스트 내 개체를 식별합니다. (예: spindle=1) 자세한 설명은 " 5 .2.1.2.2 spindle " 절에서 확인할 수 있습니다.
- feed 해당 계통의 축 이송에 대한 정보를 나타내며, feed 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.3 feed " 절에서 확인할 수 있습니다.
- workStatus 해당 계통에서 수행되는 가공 작업들의 리스트를 나타내며, workStatus 타입으로 정의됩니다. "Filter" 로 workStatus 을 사용하여 리스트 내 개체를 식별합니다. (예: workStatus=1) 자세한 설명은 " 5 .2.1.2.4 workStatus " 절에서 확인할 수 있습니다.

- activeTool 해당 계통에 활성화되어 있는 공구 정보를 나타내며, activeTool 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.4.2 activeTool/tools " 절에서 확인할 수 있습니다.
- currentProgram 해당 계통에서 현재 실행 중인 NC 프로그램에 대한 정보를 나타내며, currentProgram 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.5 currentProgram " 절에서 확인할 수 있습니다.
- workOffset 해당 계통에서 사용하는 공작물 좌표계에 대한 G 코드 및 오프셋량의 리스트를 나타내며, workOffset 타입으로 정의됩니다. "Filter" 로 workOffset 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffset=1) 자세한 설명은 " 5 .2.1.2.6 workOffset " 절에서 확인할 수 있습니다.
- alarm 해당 계통에서 발생한 알람 정보의 리스트 나타내며, alarm 타입으로 정의됩니다. "Filter" 로 alarm 을 사용하여 리스트 내 개체를 식별합니다. (예: alarm=1) 자세한 설명은 " 5 .2.1.2.7 alarm " 절에서 확인할 수 있습니다.
- variable 해당 계통에서 사용하는 변수의 리스트 나타내며, variable 타입으로 정의됩니다. "Filter" 로 variable 을 사용하여 리스트 내 개체를 식별합니다. (예: variable=1) 자세한 설명은 " 5 .2.1.2.8 variable " 절에서 확인할 수 있습니다.

---

##### 5.2.1.2.1  axis
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 axis 데이터는 축 별로 기록되는 상태 정보를 나타내며, 해당 축에 대한 식별 정보, 위치 정보, 부하 정보 등을 포함합니다.

- 데이터 구성

| Axis | | |
| ---------------------------------- | ------------ | ----------- |
| machinePosition | : REAL, | Read-only; |
| workPosition | : REAL, | Read-only; |
| distanceToGo | : REAL, | Read-only; |
| relativePostion | : REAL, | Read-only; |
| axisName | : STRING, | Read-only; |
| relativeAxisName | : STRING, | Read-only; |
| axisLoad | : REAL, | Read-only; |
| axisFeed | : REAL, | Read-only; |
| axisLimitPlus | : REAL, | Read/Write; |
| axisLimitMinus | : REAL, | Read/Write; |
| workAreaLimitPlus | : REAL, | Read/Write; |
| workAreaLimitMinus | : REAL, | Read/Write; |
| workAreaLimitPlusEnabled | : BOOLEAN, | Read/Write; |
| workAreaLimitMinusEnabled | : BOOLEAN, | Read/Write; |
| axisEnabled | : BOOLEAN, | Read-only; |
| interlockEnabled | : BOOLEAN, | Read-only; |
| constantSurfaceSpeedControlEnabled | : BOOLEAN, | Read-only; |
| axisCurrent | : REAL, | Read-only; |
| machineOrigin | : REAL, | Read/Write; |
| axisTemperature | : REAL, | Read-only; |
| axisPower | : axisPower; | |

- 구성 데이터 설명

- machinePosition 해당 축의 머신 좌표계를 기준으로 한 좌표값을 정의하는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/machinePosition?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workPosition 해당 축의 워크 좌표계를 기준으로 한 좌표값을 정의하는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/workPosition?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- distanceToGo NC 프로그램에서 지령한 위치 대비 현재 남은 이동거리에 대한 해당 축의 좌표값을 정의하는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/distanceToGo?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- relativePosition 해당 축의 상대 좌표계를 기준으로 한 좌표값을 정의하는 실수형 속성 입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/relativePosition?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisName 해당 축에 대한 절대좌표 축 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisName?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- relativeAxisName (FANUC only) 해당 축에 대한 상대좌표 축 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/relativeAxisName?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisLoad 해당 축에 걸리는 부하를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisLoad?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisFeed 해당 축에 대한 이송 속도를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisFeed?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisLimitPlus 해당 축에서 “+” 방향으로 움직일 수 있는 최대값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisLimitPlus?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisLimitMinus 해당 축에서 “-” 방향으로 움직일 수 있는 최대값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisLimitMinus?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workAreaLimitPlus 충돌방지를 위해 작업 금지영역 설정 시 해당 축에서 “+” 방향으로 움직일 수 있는 최대값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/workAreaLimitPlus?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workAreaLimitMinus 충돌방지를 위해 작업 금지영역 설정 시 해당 축에서 “-” 방향으로 움직일 수 있는 최대값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/workAreaLimitMinus?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workAreaLimitPlusEnabled workAreaLimitPlus 속성의 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/workAreaLimitPlusEnabled?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workAreaLimitMinusEnabled workAreaLimitMinus 속성의 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/workAreaLimitMinusEnabled?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- interlockEnabled 해당 축의 인터락 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/interlockEnabled?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- constantSurfaceSpeedControlEnabled 해당 축의 주속제어 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/constantSurfaceSpeedControlEnabled?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다. SIEMENS에서만 의미가 있습니다. FANUC은 축 구분을 하지 않으므로 디폴트값 1을 입력합니다.
- axisEnabled 해당 축의 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisEnabled?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisCurrent 해당 축의 전류 정보를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisCurrent?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- machineOrigin 해당 축의 초기 기계 원점에 대한 좌표값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/machineOrigin?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisTemperature 해당 축의 온도 정보를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisTemperature?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- axisPower 해당 축의 전력 정보를 나타내며, axisPower타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.1:A. axisPower " 절에서 확인할 수 있습니다.

---

## A.  axisPower
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.1 axis 

- 개요 axisPower 데이터는 CNC 공작기계 내의 축과 스핀들이 가지고 있는 전력에 대한 정보를 나타내며, 실 소비 전력의 적산값, 소비전력의 적산값, 회생전력의 적산값 등을 포함합니다.

- 데이터 구성

| axisPower | | |
| ---------------------- | ------- | ---------- |
| actualPowerConsumption | : REAL, | Read-only; |
| powerConsumption | : REAL, | Read-only; |
| regeneratedPower | : REAL, | Read-only; |

- 구성 데이터 설명

- actualPowerConsumption 해당 축에 대한 실소비 전력의 적산값을 나타내는 실수형 속성입니다. 실소비 전력은 소비전력에서 회생전력을 뺀 값입니다. (실소비 전력= 소비 전력 – 회생 전력)

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisPower/actualPowerConsumption?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- powerConsumption 해당 축에 대한 소비전력의 적산값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisPower/powerConsumption?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- regeneratedPower 해당 축에 대한 회생전력의 적산값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/axis/axisPower/regeneratedPower?machine=i&channel=j&axis=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.2 spindle
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 spindle 데이터는 스핀들별로 기록되는 상태 정보를 나타내며, 해당 스핀들의 식별 정보, 속도 정보, 부하 정보, 한계 속도 등을 포함합니다.

- 데이터 구성

| spindle | | |
| ------------------ | --------------- | ---------- |
| spindleLoad | : REAL, | Read-only; |
| spindleOverride | : REAL, | Read-only; |
| spindleLimit | : REAL, | Read-only; |
| spindleEnabled | : BOOLEAN, | Read-only; |
| spindleCurrent | : REAL, | Read-only; |
| spindleTemperature | : REAL, | Read-only; |
| rpm | : rpm; | |
| spindlePower | : spindlePower; | |

- 구성 데이터 설명

- spindleLoad 해당 스핀들에 걸리는 부하를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleLoad?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- spindleOverride 해당 스핀들의 회전 속도에 오버라이드된 비율을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleOverride?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- spindleLimit 해당 스핀들에 대한 최대 회전 속도의 한계 값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleLimit?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- spindleEnabled 해당 스핀들의 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleEnabled?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- spindleCurrent 해당 스핀들의 전류 정보를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleCurrent?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- spindleTemperature 해당 스핀들의 온도 정보를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindleTemperature?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- rpm 해당 스핀들의 회전 속도를 나타내며, rpm 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.2:A. rpm " 절에서 확인할 수 있습니다.
- spindlePower 해당 스핀들의 전력 정보를 나타내며, spindlePower타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.2:B. spindlePower " 절에서 확인할 수 있습니다.

---

## A. rpm
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.2 spindle 

- 개요 rpm 데이터는 CNC 공작기계에서 나타나는 스핀들 회전속도에 대한 정보를 나타내며, 지령된 속도와 실제 측정된 속도 값, 속도의 단위 정보를 포함합니다.

- 데이터 구성

| rpm | | |
| -------------- | ---------- | ---------- |
| commandedSpeed | : REAL, | Read-only; |
| actualSpeed | : REAL, | Read-only; |
| speedUnit | : INTEGER, | Read-only; |

- 구성 데이터 설명

- commandedSpeed NC 프로그램이나 MDI를 통해 지령된 스핀들 회전속도 값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/rpm/commandedSpeed?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- actualSpeed 지령된 스핀들 회전속도 값에 대해서 실제로 측정된 스핀들 회전속도 값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/rpm/actualSpeed?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- speedUnit 지령된 스핀들 회전속도 및 측정된 스핀들 회전속도 값의 단위 정보를 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/rpm/speedUnit?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ---------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : mm/min | O | O | | | |
| 1 : inch/min | O | O | | | |
| 2 : rpm(rev/min) | O | O | O | O | O |
| 3 : mm/rev | O | O | | | |
| 4 : inch/rev | O | O | | | |

---

## B. spindlePower
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.2 spindle 

- 개요 spindlePower 데이터는 CNC 공작기계 내의 축과 스핀들이 가지고 있는 전력에 대한 정보를 나타내며, 실 소비 전력의 적산값, 소비전력의 적산값, 회생전력의 적산값 등을 포함합니다.

- 데이터 구성

| spindlePower | | |
| ---------------------- | ------- | ---------- |
| actualPowerConsumption | : REAL, | Read-only; |
| powerConsumption | : REAL, | Read-only; |
| regeneratedPower | : REAL, | Read-only; |

- 구성 데이터 설명

- actualPowerConsumption 해당 스핀들에 대한 실소비 전력의 적산값을 나타내는 실수형 속성입니다. 실소비 전력은 소비전력에서 회생전력을 뺀 값입니다. (실소비 전력= 소비 전력 – 회생 전력)

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindlePower/actualPowerConsumption?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- powerConsumption 해당 스핀들에 대한 소비전력의 적산값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindlePower/powerConsumption?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다.
- regeneratedPower 해당 스핀들에 대한 회생전력의 적산값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/spindle/spindlePower/regeneratedPower?machine=i&channel=j&spindle=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 스핀들인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.3 feed
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 feed 데이터는 축 이송에 대한 정보를 나타내며, 가공 이송속도, 가공 이송속도에 대한 오버라이드, 급속 이송에 대한 오버라이드 정보 등을 포함합니다.

- 데이터 구성

| feed | | |
| ------------- | ----------- | ---------- |
| feedOverride | : REAL, | Read-only; |
| rapidOverride | : REAL, | Read-only; |
| feedRate | : feedRate; | |

- 구성 데이터 설명

- feedOverride 이송 속도에 오버라이드된 비율을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/feed/feedOverride?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- rapidOverride 급속 이송 속도에 오버라이드된 비율을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/feed/rapidOverride?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- feedRate 이송 속도를 나타내며, feedRate 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.3:A. feedRate " 절에서 확인할 수 있습니다.

---

## A. feedRate
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.3 feed 

- 개요 feedRate 데이터는 이송속도에 대한 정보를 나타내며, 지령된 속도와 실제 측정된 속도 값, 속도의 단위 정보를 포함합니다.

- 데이터 구성

| feedRate | | |
| -------------- | ---------- | ---------- |
| commandedSpeed | : REAL, | Read-only; |
| actualSpeed | : REAL, | Read-only; |
| speedUnit | : INTEGER, | Read-only; |

- 구성 데이터 설명

- commandedSpeed NC 프로그램이나 MDI를 통해 지령된 이송속도 값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/feed/feedRate/commandedSpeed?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- actualSpeed 지령된 이송속도 값에 대해서 실제로 측정된 이송속도 값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/feed/feedRate/actualSpeed?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- speedUnit 지령된 이송속도 및 측정된 이송속도 값의 단위 정보를 나타내는 데이터입니다. 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/feed/feedRate/speedUnit?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ---------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : mm/min | O | O | O | O | O |
| 1 : inch/min | O | O | | | |
| 2 : rpm(rev/min) | O | O | | | |
| 3 : mm/rev | O | O | | | |
| 4 : inch/rev | O | O | | | |

---

##### 5.2.1.2.4 workStatus
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 workStatus 데이터는 장비에 할당된 가공 작업들의 진척 상태에 대한 정보를 나타내며, 가공 수량 정보, 가공 시간 등을 포함합니다.

- 데이터 구성

| workStatus | | |
| ------------- | ---------------- | --- |
| workCounter | : workCounter; | |
| machiningTime | : machiningTime; | |

- 구성 데이터 설명

- workCounter 장비의 가공 수량에 대한 정보를 나타내며, workCounter 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.4:A. workCounter " 절에서 확인할 수 있습니다.
- machiningTime 현재 가공 중인 아이템의 가공 시간에 대한 정보를 나타내며, machiningTime 으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.4:B. machiningTime " 절에서 확인할 수 있습니다.

---

## A. workCounter
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.4 workStatus 

- 개요 workCounter 데이터는 가공 수량에 대한 정보를 나타내며, 현재 가공 수량, 목표 가공 수량에 대한 정보를 포함합니다.

- 데이터 구성

| workCounter | | |
| ------------------ | ---------- | ----------- |
| currentWorkCounter | : INTEGER, | Read/Write; |
| targetWorkCounter | : INTEGER, | Read/Write; |
| totalWorkCounter | : INTEGER, | Read/Write; |

- 구성 데이터 설명

- currentWorkCounter 현재까지 가공된 아이템의 수량을 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/workCounter/currentWorkCounter?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다.
- targetWorkCounter 가공하고자 하는 아이템의 목표 수량을 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/workCounter/targetWorkCounter?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다.
- totalWorkCounter 총 가공 수량을 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/workCounter/totalWorkCounter?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다. 

---

## B. machiningTime
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.4 workStatus 

- 개요 machiningTime 데이터는 가공 시간에 대한 정보를 나타내며, 현재 가공이 진행된 시간, 가공이 완료되기까지 걸릴 것으로 예측되는 시간 정보를 포함합니다.

- 데이터 구성

| machiningTime | | |
| ----------------------- | ------- | ---------- |
| processingMachiningTime | : REAL, | Read-only; |
| estimatedMachiningTime | : REAL, | Read-only; |
| machineOperationTime | : REAL, | Read-only; |
| actualCuttingTime | : REAL, | Read-only; |

- 구성 데이터 설명

- processingMachiningTime 현재 가공이 진행된 시간을 나타내는 실수형 속성입니다. (단위 : 초)

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/machiningTime/processingMachiningTime?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다.
- estimatedMachiningTime (SIEMENS only) 현재 진행 중인 가공이 완료되기까지 걸릴 것으로 예측되는 시간을 나타내는 실수형 속성입니다. (단위 : 초)

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/machiningTime/estimatedMachiningTime?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다.
- machineOperationTime 자동 운전 모드에서 해당 장비의 운전시간을 나타내는 실수형 속성입니다.  (단위 : 초)

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/machiningTime/machineOperationTime?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다.
- actualCuttingTime 해당 장비의 절삭시간을 나타내는 실수형 속성입니다.  (단위 : 초)

주소 표기는 다음과 같이 합니다. data://machine/channel/workStatus/machiningTime/actualCuttingTime?machine=i&channel=j&workStatus=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 작업물인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.5 currentProgram
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 currentProgram 데이터는 실행 중인 NC 프로그램의 진행 상태 정보를 나타내며, 프로그램 기본 정보와 함께 프로그램 내의 현재 시퀀스 정보, 블록 카운터 정보 등을 포함합니다.

- 데이터 구성

| currentProgram | | |
| ---------------------- | --------------------------------- | ---------- |
| sequenceNumber | : INTEGER, | Read-only; |
| currentBlockCounter | : INTEGER, | Read-only; |
| lastBlock | : STRING, | Read-only; |
| currentBlock | : STRING, | Read-only; |
| nextBlock | : STRING, | Read-only; |
| activePartProgram | : STRING, | Read-only; |
| programMode | : INTEGER, | Read-only; |
| currentWorkOffsetIndex | : INTEGER, | Read-only; |
| currentWorkOffsetCode | : STRING, | Read-only; |
| currentDepthLevel | : INTEGER, | Read-only; |
| modal | : LIST [1:N] OF “modal”; | |
| overallBlock | : LIST [1:N] OF “overallBlock”; | |
| interruptBlock | : LIST [1:N] OF “interruptBlock”; | |
| currentTotalWorkOffset | : currentTotalWorkOffset; | |
| currentFile | : currentFile; | |
| mainFile | : mainFile; | |
| controlOption | : controlOption; | |

- 구성 데이터 설명

- sequenceNumber 실행 중인 NC 프로그램의 시퀀스 번호를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/sequenceNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- currentBlockCounter 실행 중인 NC 프로그램의 블록 카운터를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentBlockCounter?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- lastBlock 실행 중인 NC 프로그램의 이전 블록 정보를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/lastBlock?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- currentBlock 실행 중인 NC 프로그램의 현재 블록 정보를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentBlock?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- nextBlock 실행 중인 NC 프로그램의 다음 블록 정보를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/nextBlock?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- activePartProgram 실행 중인 NC 프로그램의 블록 정보를 최대 200자까지 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/activePartProgram?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programMode 실행 중인 NC 프로그램의 실행 모드를 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/programMode?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ------------------------ | ----- | ------- | ----- | ---------- | ---- |
| 0 : **** (reset) | O | O | O | O | O |
| 1 : Stop | O | O | O | O | O |
| 2 : Hold | O | | O | | O |
| 3 : Start (Active) (Run) | O | O | O | O | O |
| 4 : MSTR | O | | | | |
| 5 : Interrupted | | O | | | |
| 6 : Pause | | | | O | |
| 7 : Waiting | | O | | | |

- currentWorkOffsetIndex 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드를 나타내는 정수형 속성입니다. 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentWorkOffsetIndex?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| FANUC | SIEMENS | MITSUBISHI | KCNC |
| --------------- | ------------ | ---------- | ------- |
| | 0 : G500 | | |
| 1 : G54 | 1 : G54 | 1 : G54 | 1 : G54 |
| 2 : G55 | 2 : G55 | 2 : G55 | 2 : G55 |
| 3 : G56 | 3 : G56 | 3 : G56 | 3 : G56 |
| 4 : G57 | 4 : G57 | 4 : G57 | 4 : G57 |
| 5 : G58 | 5 : G505 | 5 : G58 | 5 : G58 |
| 6 : G59 | 6 : G506 | 6 : G59 | 6 : G59 |
| 7 : G54.1P1 | : | 7 : G54.1 | |
| : | : | | |
| n : G54.1P(n-6) | n : G(500+n) | | |
| : | : | | |
| 306 : G54.1P300 | 99 : G599 | | |

- currentWorkOffsetCode 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드를 나타내는 문자열 속성입니다. currentWorkOffsetIndex에 해당하는 G 코드 문자열입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentWorkOffsetCode?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- currentDepthLevel 실행 중인 NC 프로그램의 프로그램 레벨을 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentDepthLevel?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| 결과 | SIEMENS | MITSUBISHI |
| --- | ------------------------------------- | ---------- |
| 0 | | O |
| 1 | O : Main program | O |
| 2 | O : 1st subroutine level | O |
| 3 | O : 2nd subroutine level | O |
| 4 | O : 3rd subroutine level | O |
| 5 | O : 4th subroutine level | O |
| 6 | O : 5th subroutine level | O |
| 7 | O : 6th subroutine level | O |
| 8 | O : 7th subroutine level | O |
| 9 | O : 1st asynchronous subroutine level | |
| 10 | O : 2nd asynchronous subroutine level | |
| 11 | O : 3rd asynchronous subroutine level | |
| 12 | O : 4th asynchronous subroutine level | |

- modal 실행 중인 NC 프로그램에서 사용하고 있는 G 코드들의 리스트를 나타내며, 각 G 코드는 modal 타입으로 정의됩니다. "Filter" 로 modal 을 사용하여 리스트 내 개체를 식별합니다. (예: modal=1) 자세한 설명은 " 5 .2.1.2.5:A. modal " 절에서 확인할 수 있습니다.

- overallBlock 실행 중인 블록들에 대한 리스트를 나타내며, 각 블록은 overallBlock 타입으로 정의됩니다. 해당 블록을 포함하고 있는 프로그램의 레벨과 이름, 블록 카운터, 블록 데이터와 같은 속성을 포함합니다.  "Filter" 로 overallblock 을 사용하여 리스트 내 개체를 식별합니다. (예: overallblock=1) 자세한 설명은 " 5 .2.1.2.5:B. overallblock " 절에서 확인할 수 있습니다.
- interruptBlock 실행 중인 NC 프로그램이 중단되었을 때, 중단의 원인이 되는 블록들에 대한 리스트를 나타내며, interruptBlock 타입으로 정의됩니다. 해당 블록을 포함하고 있는 프로그램의 레벨과 이름, 블록 카운터, 블록 데이터와 같은 속성을 포함합니다.  "Filter" 로 interruptblock 을 사용하여 리스트 내 개체를 식별합니다. (예: interruptblock=1) 자세한 설명은 " 5 .2.1.2.5:C. interruptblock " 절에서 확인할 수 있습니다.

- currentTotalWorkOffset 실행 중인 NC 프로그램의 공작물 좌표계 관련 G 코드에 대한 총 오프셋량을 나타내며, currentTotalWorkOffset 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.5:D. currentTotalWorkOffset " 절에서 확인할 수 있습니다.
- currentFile 실행 중인 NC 프로그램의 기본 파일 정보를 나타내며, currentFile 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.5:E. currentFile " 절에서 확인할 수 있습니다.

- mainFile 실행 중인 NC 프로그램과는 별개로, 현재 선택되어 있는 NC 프로그램에 대한 파일 정보를 나타내며, mainFile 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.5:F. mainFile " 절에서 확인할 수 있습니다.

- controlOption singleBlock, dryRun, optionalStop, blockSkip, machineLock 등과 같이 실행 중인 NC 프로그램의 제어 환경을 나타내며, controlOption 타입으로 정의됩니다. 자세한 설명은 " 5 .2.1.2.5:G. controlOption " 절에서 확인할 수 있습니다.

---

## A. modal
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 modal 데이터는 실행 중인 NC 프로그램에서 사용하고 있는 G 코드에 대한 정보를 나타내며, G코드 내 그룹 번호, G 코드 데이터를 포함합니다.

- 데이터 구성

| modal | | |
| ---------- | ---------- | ---------- |
| modalIndex | : INTEGER, | Read-only; |
| modalCode | : STRING, | Read-only; |

- 구성 데이터 설명

- modalIndex 각 NC 의 그룹 번호에 따라 G 코드 인덱스를 나타내는 정수형 속성입니다. 각 NC 에서 이용 가능한 값들과 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/modal/modalIndex?machine=i&channel=j&modalIndex=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 각 NC제조사가 지정한 그룹 번호를 의미하는 정수값입니다. [FANUC G그룹 번호와 G코드 인덱스 데이터]

| G group number | Index | M | T | | |
| -------------- | --------------- | --------------- | --------------- | ------------ | ------------ |
| Code | Code (System A) | Code (System B) | Code (System C) | | |
| 0 | 0 | G00 | G00 | G00 | G00 |
| 1 | G01 | G01 | G01 | G01 | |
| 2 | G02 | G02 | G02 | G02 | |
| 3 | G03 | G03 | G03 | G03 | |
| 4 | G33 | G32 | G33 | G33 | |
| 5 | G75 | G90 | G77 | G20 | |
| 6 | G77 | G92 | G78 | G21 | |
| 7 | G78 | G94 | G79 | G24 | |
| 8 | G79 | - | - | - | |
| 9 | - | G34 | G34 | G34 | |
| 10 | G02.2 | - | - | - | |
| 11 | G03.2 | - | - | - | |
| 12 | G02.3 | - | - | - | |
| 13 | G03.3 | - | - | - | |
| 14 | G06.2 | G35 | G35 | G35 | |
| 15 | G02.4 | G36 | G36 | G36 | |
| 16 | G03.4 | - | - | - | |
| 17 | - | G06.2 | G06.2 | G06.2 | |
| 18 | - | G02.4 | G02.4 | G02.4 | |
| 19 | - | G03.4 | G03.4 | G03.4 | |
| 20 | - | G02.2 | G02.2 | G02.2 | |
| 21 | - | G03.2 | G03.2 | G03.2 | |
| 22 | G35 | G02.3 | G02.3 | G02.3 | |
| 23 | G36 | G03.3 | G03.3 | G03.3 | |
| 24 | G34 | G06.1 | G06.1 | G06.1 | |
| 25 | - | G32.2 | G32.2 | G32.2 | |
| 1 | 0 | G17 | G97 | G97 | G97 |
| 1 | - | G96 | G96 | G96 | |
| 4 | G19 | - | - | - | |
| 8 | G18 | - | - | - | |
| 10 | G17.1 | - | - | - | |
| 2 | 0 | G90 | - | G90 | G90 |
| 1 | G91 | - | G91 | G91 | |
| 3 | 0 | G23 | G69 | G69 | G69 |
| 1 | G22 | G68 | G68 | G68 | |
| 4 | 0 | G94 | G98 | G94 | G94 |
| 1 | G95 | G99 | G95 | G95 | |
| 2 | G93 | G93 | G93 | G93 | |
| 3 | G93.2 | G93 | G93 | G93 | |
| 5 | 0 | G20(G70) | G20 | G20 | G20 |
| 1 | G21(G71) | G21 | G21 | G21 | |
| 6 | 0 | G40 | G40 | G40 | G40 |
| 1 | G41 | G41 | G41 | G41 | |
| 2 | G42 | G42 | G42 | G42 | |
| 3 | G41.2 | G41.2 | G41.2 | G41.2 | |
| 4 | G42.2 | G42.2 | G42.2 | G42.2 | |
| 5 | G41.3 | G41.3 | G41.3 | G41.3 | |
| 6 | G41.4 | G41.4 | G41.4 | G41.4 | |
| 7 | G42.4 | G42.4 | G42.4 | G42.4 | |
| 8 | G41.5 | G41.5 | G41.5 | G41.5 | |
| 9 | G42.5 | G42.5 | G42.5 | G42.5 | |
| 10 | G41.6 | G40.3 | G40.3 | G40.3 | |
| 11 | G42.6 | G41.6 | G41.6 | G41.6 | |
| 12 | - | G42.6 | G42.6 | G42.6 | |
| 7 | 0 | G49(G49.1) | G25 | G25 | G25 |
| 1 | G43 | G26 | G26 | G26 | |
| 2 | G44 | - | - | - | |
| 3 | G43.1 | - | - | - | |
| 4 | G43.4 | - | - | - | |
| 5 | G43.5 | - | - | - | |
| 6 | G43.2 | - | - | - | |
| 7 | G43.3 | - | - | - | |
| 8 | 0 | G80 | G23 | G23 | G23 |
| 1 | G81 | G22 | G22 | G22 | |
| 2 | G82 | - | - | - | |
| 3 | G83 | - | - | - | |
| 4 | G84 | - | - | - | |
| 5 | G85 | - | - | - | |
| 6 | G86 | - | - | - | |
| 7 | G87 | - | - | - | |
| 8 | G88 | - | - | - | |
| 9 | G89 | - | - | - | |
| 10 | G73 | - | - | - | |
| 11 | G74 | - | - | - | |
| 12 | G76 | - | - | - | |
| 13 | G84.2 | - | - | - | |
| 14 | G84.3 | - | - | - | |
| 15 | G81.2 | - | - | - | |
| 9 | 0 | G98 | G80 | G80 | G80 |
| 1 | G99 | G83 | G83 | G83 | |
| 2 | - | G84 | G84 | G84 | |
| 3 | - | G85 | G85 | G85 | |
| 4 | - | G86 | G86 | G86 | |
| 5 | - | G87 | G87 | G87 | |
| 6 | - | G88 | G88 | G88 | |
| 7 | - | G89 | G89 | G89 | |
| 10 | 0 | G50 | - | G98 | G98 |
| 1 | G51 | - | G99 | G99 | |
| 11 | 0 | G67 | G67 | G67 | G67 |
| 1 | G66 | G66 | G66 | G66 | |
| 2 | G66.1 | G66.1 | G66.1 | G66.1 | |
| 12 | 0 | G97 | G49 | G49 | G49 |
| 1 | G96 | G43 | G43 | G43 | |
| 13 | 0 | G54(G54.1) | G54 | G54 | G54 |
| 1 | G55 | G55 | G55 | G55 | |
| 2 | G56 | G56 | G56 | G56 | |
| 3 | G57 | G57 | G57 | G57 | |
| 4 | G58 | G58 | G58 | G58 | |
| 5 | G59 | G59 | G59 | G59 | |
| 14 | 0 | G64 | G64 | G64 | G64 |
| 1 | G61 | G61 | G61 | G61 | |
| 2 | G62 | G62 | G62 | G62 | |
| 3 | G63 | G63 | G63 | G63 | |
| 15 | 0 | G69 | G17 | G17 | G17 |
| 1 | G68 | - | - | - | |
| 2 | G68.2 | - | - | - | |
| 3 | G68.3 | - | - | - | |
| 4 | - | G18 | G18 | G18 | |
| 8 | - | G19 | G19 | G19 | |
| 10 | - | G17.1 | G17.1 | G17.1 | |
| 16 | 0 | G15 | G69.1 | G69.1 | G69.1 |
| 1 | G16 | G68.1 | G68.1 | G68.1 | |
| 2 | - | G68.2 | G68.2 | G68.2 | |
| 17 | 0 | G40.1 (G150) | - | G50 | G50 |
| 1 | G41.1 (G151) | - | G51 | G51 | |
| 2 | G42.1 (G152) | - | - | - | |
| 18 | 0 | G25 | - | - | - |
| 1 | G26 | - | - | - | |
| 19 | 0 | G160 | G50.2 | G50.2 | G50.2 |
| 1 | G161 | G51.2 | G51.2 | G51.2 | |
| 20 | 0 | G13.1 (G113) | G13.1 (G113) | G13.1 (G113) | G13.1 (G113) |
| 1 | G12.1 (G112) | G12.1 (G112) | G12.1 (G112) | G12.1 (G112) | |

[SIEMENS G그룹 번호와 G코드 인덱스 데이터]

| G group number | Index | Code |
| -------------- | ----------- | --------- |
| 1 | 1 | G0 |
| 2 | G1 | |
| 3 | G2 | |
| 4 | G3 | |
| 5 | CIP | |
| 6 | ASPLINE | |
| 7 | BSPLINE | |
| 8 | CSPLINE | |
| 9 | POLY | |
| 10 | G33 | |
| 11 | G331 | |
| 12 | G332 | |
| 13 | OEMIPO1 | |
| 14 | OEMIPO2 | |
| 15 | CT | |
| 16 | G34 | |
| 17 | G35 | |
| 18 | INVCW | |
| 19 | INVCCW | |
| 20 | G335 | |
| 21 | G336 | |
| 2 | 1 | G4 |
| 2 | G63 | |
| 3 | G74 | |
| 4 | G75 | |
| 5 | REPOSL | |
| 6 | REPOSQ | |
| 7 | REPOSH | |
| 8 | REPOSA | |
| 9 | REPOSQA | |
| 10 | REPOSHA | |
| 11 | G147 | |
| 12 | G247 | |
| 13 | G347 | |
| 14 | G148 | |
| 15 | G248 | |
| 16 | G348 | |
| 17 | G5 | |
| 18 | G7 | |
| 3 | 1 | TRANS |
| 2 | ROT | |
| 3 | SCALE | |
| 4 | MIRROR | |
| 5 | ATRANS | |
| 6 | AROT | |
| 7 | ASCALE | |
| 8 | AMIRROR | |
| 10 | G25 | |
| 11 | G26 | |
| 12 | G110 | |
| 13 | G111 | |
| 14 | G112 | |
| 16 | G59 | |
| 17 | ROTS | |
| 18 | AROTS | |
| 4 | 1 | STARTFIFO |
| 2 | STOPFIFO | |
| 3 | FIFOCTRL | |
| 6 | 1 | G17 |
| 2 | G18 | |
| 3 | G19 | |
| 7 | 1 | G40 |
| 2 | G41 | |
| 3 | G42 | |
| 8 | 1 | G500 |
| 2 | G54 | |
| 3 | G55 | |
| 4 | G56 | |
| 5 | G57 | |
| 6 | G505 | |
| ... | ... | |
| 100 | G599 | |
| 9 | 1 | G53 |
| 2 | SUPA | |
| 3 | G153 | |
| 10 | 1 | G60 |
| 2 | G64 | |
| 3 | G641 | |
| 4 | G642 | |
| 5 | G643 | |
| 6 | G644 | |
| 7 | G645 | |
| 11 | 1 | G9 |
| 12 | 1 | G601 |
| 2 | G602 | |
| 3 | G603 | |
| 13 | 1 | G70 |
| 2 | G71 | |
| 3 | G700 | |
| 4 | G710 | |
| 14 | 1 | G90 |
| 2 | G91 | |
| 15 | 1 | G93 |
| 2 | G94 | |
| 3 | G95 | |
| 4 | G96 | |
| 5 | G97 | |
| 6 | G931 | |
| 7 | G961 | |
| 8 | G971 | |
| 9 | G942 | |
| 10 | G952 | |
| 11 | G962 | |
| 12 | G972 | |
| 13 | G973 | |
| 16 | 1 | CFC |
| 2 | CFTCP | |
| 3 | CFIN | |
| 17 | 1 | NORM |
| 2 | KONT | |
| 3 | KONTT | |
| 4 | KONTC | |
| 18 | 1 | G450 |
| 2 | G451 | |
| 19 | 1 | BNAT |
| 2 | BTAN | |
| 3 | BAUTO | |
| 20 | 1 | ENAT |
| 2 | ETAN | |
| 3 | EAUTO | |
| 21 | 1 | BRISK |
| 2 | SOFT | |
| 3 | DRIVE | |
| 22 | 1 | CUT2D |
| 2 | CUT2DF | |
| 3 | CUT3DC | |
| 4 | CUT3DF | |
| 5 | CUT3DFS | |
| 6 | CUT3DFF | |
| 7 | CUT3DCC | |
| 8 | CUT3DCCD | |
| 9 | CUT2DD | |
| 10 | CUT2DFD | |
| 11 | CUT3DCD | |
| 23 | 1 | CDOF |
| 2 | CDON | |
| 3 | CDOF2 | |
| 24 | 1 | FFWOF |
| 2 | FFWON | |
| 25 | 1 | ORIWKS |
| 2 | ORIMKS | |
| 26 | 1 | RMB |
| 2 | RMI | |
| 3 | RME | |
| 4 | RMN | |
| 27 | 1 | ORIC |
| 2 | ORID | |
| 28 | 1 | WALIMON |
| 2 | WALIMOF | |
| 29 | 1 | DIAMOF |
| 2 | DIAMON | |
| 3 | DIAM90 | |
| 4 | DIAMCYCOF | |
| 30 | 1 | COMPOF |
| 2 | COMPON | |
| 3 | COMPCURV | |
| 4 | COMPCAD | |
| 5 | COMPSURF | |
| 31 | 1 | G810 |
| 2 | G811 | |
| 3 | G812 | |
| 4 | G813 | |
| 5 | G814 | |
| 6 | G815 | |
| 7 | G816 | |
| 8 | G817 | |
| 9 | G818 | |
| 10 | G819 | |
| 32 | 1 | G820 |
| 2 | G821 | |
| 3 | G822 | |
| 4 | G823 | |
| 5 | G824 | |
| 6 | G825 | |
| 7 | G826 | |
| 8 | G827 | |
| 9 | G828 | |
| 10 | G829 | |
| 33 | 1 | FTOCOF |
| 2 | FTOCON | |
| 34 | 1 | OSOF |
| 2 | OSC | |
| 3 | OSS | |
| 4 | OSSE | |
| 5 | OSD | |
| 6 | OST | |
| 35 | 1 | SPOF |
| 2 | SON | |
| 3 | PON | |
| 4 | SONS | |
| 5 | PONS | |
| 36 | 1 | PDELAYON |
| 2 | PDELAYOF | |
| 37 | 1 | FNORM |
| 2 | FLIN | |
| 3 | FCUB | |
| 38 | 1 | SPIF1 |
| 2 | SPIF2 | |
| 39 | 1 | CPRECOF |
| 2 | CPRECON | |
| 40 | 1 | CUTCONOF |
| 2 | CUTCONON | |
| 41 | 1 | LFOF |
| 2 | LFON | |
| 42 | 1 | TCOABS |
| 2 | TCOFR | |
| 3 | TCOFRZ | |
| 4 | TCOFRY | |
| 5 | TCOFRX | |
| 43 | 1 | G140 |
| 2 | G141 | |
| 3 | G142 | |
| 4 | G143 | |
| 44 | 1 | G340 |
| 2 | G341 | |
| 45 | 1 | SPATH |
| 2 | UPATH | |
| 46 | 1 | LFTXT |
| 2 | LFWP | |
| 3 | LFPOS | |
| 47 | 1 | G290 |
| 2 | G291 | |
| 48 | 1 | G460 |
| 2 | G461 | |
| 3 | G462 | |
| 49 | 1 | CP |
| 2 | PTP | |
| 3 | PTPG0 | |
| 4 | PTPWOC | |
| 50 | 1 | ORIEULER |
| 2 | ORIRPY | |
| 3 | ORIVIRT1 | |
| 4 | ORIVIRT2 | |
| 5 | ORIAXPOS | |
| 6 | ORIRPY2 | |
| 51 | 1 | ORIVECT |
| 2 | ORIAXES | |
| 3 | ORIPATH | |
| 4 | ORIPLANE | |
| 5 | ORICONCW | |
| 6 | ORICONCCW | |
| 7 | ORICONIO | |
| 8 | ORICONTO | |
| 9 | ORICURVE | |
| 10 | ORIPATHS | |
| 52 | 1 | PAROTOF |
| 2 | PAROT | |
| 53 | 1 | TOROTOF |
| 2 | TOROT | |
| 3 | TOROTZ | |
| 4 | TOROTY | |
| 5 | TOROTX | |
| 6 | TOFRAME | |
| 7 | TOFRAMEZ | |
| 8 | TOFRAMEY | |
| 9 | TOFRAMEX | |
| 54 | 1 | ORIROTA |
| 2 | ORIROTR | |
| 3 | ORIROTT | |
| 4 | ORIROTC | |
| 55 | 1 | RTLION |
| 2 | RTLIOF | |
| 56 | 1 | TOWSTD |
| 2 | TOWMCS | |
| 3 | TOWWCS | |
| 4 | TOWBCS | |
| 5 | TOWTCS | |
| 6 | TOWKCS | |
| 57 | 1 | FENDNORM |
| 2 | G62 | |
| 3 | G621 | |
| 59 | 1 | DYNNORM |
| 2 | DYNPOS | |
| 3 | DYNROUGH | |
| 4 | DYNSEMIFIN | |
| 5 | DYNFINISH | |
| 60 | 1 | WALCS0 |
| 2 | WALCS1 | |
| 3 | WALCS2 | |
| 4 | WALCS3 | |
| 5 | WALCS4 | |
| 6 | WALCS5 | |
| 7 | WALCS6 | |
| 8 | WALCS7 | |
| 9 | WALCS8 | |
| 10 | WALCS9 | |
| 11 | WALCS10 | |
| 61 | 1 | ORISOF |
| 2 | ORISON | |
| 62 | 1 | RMBBL |
| 2 | RMIBL | |
| 3 | RMEBL | |
| 4 | RMNBL | |
| 64 | 1 | GFRAME[0] |
| 2 | GFRAME[1] | |
| 3 | GFRAME[2] | |
| ... | ... | |
| 101 | GFRAME[100] | |

[MITSUBISHI G그룹 번호와 G코드 인덱스 데이터]

| G group number | Index | Code |
| -------------- | ----- | ----- |
| 1 | 1 | G00 |
| 2 | G01 | |
| 3 | G02 | |
| 4 | G03 | |
| 5 | G33 | |
| 6 | G02.1 | |
| 7 | G03.1 | |
| 8 | G02.3 | |
| 9 | G03.3 | |
| 10 | G02.4 | |
| 11 | G03.4 | |
| 12 | G06.2 | |
| 2 | 1 | G17 |
| 2 | G18 | |
| 3 | G19 | |
| 3 | 1 | G90 |
| 2 | G91 | |
| 4 | 1 | G22 |
| 2 | G23 | |
| 5 | 1 | G93 |
| 2 | G94 | |
| 3 | G95 | |
| 6 | 1 | G20 |
| 2 | G21 | |
| 7 | 1 | G40 |
| 2 | G41 | |
| 3 | G42 | |
| 4 | G41.2 | |
| 5 | G42.2 | |
| 8 | 1 | G43 |
| 2 | G44 | |
| 3 | G43.1 | |
| 4 | G43.4 | |
| 5 | G43.5 | |
| 6 | G49 | |
| 9 | 1 | G70 |
| 2 | G71 | |
| 3 | G72 | |
| 4 | G73 | |
| 5 | G74 | |
| 6 | G75 | |
| 7 | G76 | |
| 8 | G77 | |
| 9 | G78 | |
| 10 | G79 | |
| 11 | G80 | |
| 12 | G81 | |
| 13 | G82 | |
| 14 | G83 | |
| 15 | G84 | |
| 16 | G85 | |
| 17 | G86 | |
| 18 | G87 | |
| 19 | G88 | |
| 20 | G89 | |
| 10 | 1 | G98 |
| 2 | G99 | |
| 11 | 1 | G50 |
| 2 | G51 | |
| 12 | 1 | G54 |
| 2 | G54.1 | |
| 3 | G55 | |
| 4 | G56 | |
| 5 | G57 | |
| 6 | G58 | |
| 7 | G59 | |
| 13 | 1 | G61 |
| 2 | G61.1 | |
| 3 | G61.2 | |
| 4 | G62 | |
| 5 | G63 | |
| 6 | G63.1 | |
| 7 | G63.2 | |
| 8 | G64 | |
| 14 | 1 | G66 |
| 2 | G66.1 | |
| 3 | G67 | |
| 15 | 1 | G40.1 |
| 2 | G41.1 | |
| 3 | G42.1 | |
| 16 | 1 | G68 |
| 2 | G68.2 | |
| 3 | G68.3 | |
| 4 | G69 | |
| 17 | 1 | G96 |
| 2 | G97 | |
| 18 | 1 | G15 |
| 2 | G16 | |
| 19 | 1 | G50.1 |
| 2 | G51.1 | |
| 20 | 1 | G43.1 |
| 2 | G44.1 | |
| 3 | G47.1 | |
| 21 | 1 | G07.1 |
| 2 | G107 | |
| 3 | G12.1 | |
| 4 | G112 | |
| 5 | G13.1 | |
| 6 | G113 | |

- modalCode 각 NC 의 그룹 번호에 따라 G 코드 데이터를 나타내는 문자열 속성입니다. modalIndex에 해당하는 G코드 문자열입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/modal/modalCode?machine=i&channel=j&modalCode=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 각 NC제조사가 지정한 그룹 번호를 의미하는 정수값입니다. 

---

## B. overallBlock
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 overallBlock 데이터는 실행 중인 블록 정보를 나타내며, 해당 블록에 대한 프로그램의 레벨과 이름, 블록 카운터 등을 포함합니다.

- 데이터 구성

| overallBlock | | |
| ------------ | ---------- | ---------- |
| blockCounter | : INTEGER, | Read-only; |
| programName | : STRING, | Read-only; |

- 구성 데이터 설명

- blockCounter (SIEMENS only) 프로그램 레벨에 따라 실행 중인 블록 카운터를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/overallBlock/blockCounter?machine=i&channel=j&overallBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.
- programName (SIEMENS only) 프로그램 레벨에 따라 실행 중인 NC 프로그램의 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/overallBlock/programName?machine=i&channel=j&overallBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다. 

---

## C. interruptBlock
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 interruptBlock 데이터는 중단된 NC 프로그램에서 중단의 원인이 되는 블록에 대한 정보를 나타내며, 해당 블록에 대한 프로그램의 레벨과 이름, 블록 카운터, 블록 데이터 등을 포함합니다.

- 데이터 구성

| interruptBlock | | |
| --------------- | ---------- | ---------- |
| depthLevel | : INTEGER, | Read-only; |
| blockCounter | : INTEGER, | Read-only; |
| programName | : STRING, | Read-only; |
| blockData | : STRING, | Read-only; |
| searchType | : INTEGER, | Read-only; |
| mainProgramName | : STRING, | Read-only; |

- 구성 데이터 설명

- depthLevel (SIEMENS only) 중단점의 블록이 포함된 NC 프로그램의 프로그램 레벨을 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/depthLevel?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.
- blockCounter (SIEMENS only)

프로그램 레벨에 따라 중단점의 블록에 대한 블록 카운터를 나타내는 정수형 속성입니다. 주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/blockCounter?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.
- programName (SIEMENS only) 프로그램 레벨에 따라 중단점의 블럭이 포함된 NC 프로그램의 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/programName?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.
- blockData (SIEMENS only) 프로그램 레벨에 따라 중단점의 블럭 데이터를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/blockData?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.
- searchType (SIEMENS only) 프로그램 레벨에 따라 중단점의 검색 유형을 나타내며, 각 NC 에서 이용 가능한 값들과 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/searchType?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다.

| SIEMENS |
| ----------------------------------------------------------- |
| 1: block number |
| 2: label |
| 3: string |
| 4: program level |
| 5: search pointer block-oriented (searching for line feeds) |

- mainProgramName (SIEMENS only) 프로그램 레벨에 따라 중단점에 대한 메인 프로그램의 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/interruptBlock/mainProgramName?machine=i&channel=j&interruptBlock=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 프로그램 레벨인지를 의미하는 정수값입니다. 

---

## D. currentTotalWorkOffset
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 currentTotalWorkOffset 데이터는 실행 중인 NC 프로그램의 공작물 좌표계 관련 G 코드에 대한 총 오프셋량 정보를 나타내며, G 코드 인덱스, 축별 총 오프셋 량 리스트, 축별 총 오프셋 회전량 리스트, 축별 총 오프셋 확대량 리스트, 축별 총 오프셋 미러링 여부 리스트 등을 포함합니다.

- 데이터 구성

| currentTotalWorkOffset | | |
| -------------------------- | ------------------------ | ---------- |
| workOffsetIndex | : INTEGER; | Read only; |
| workOffsetCode | : STRING, | Read only; |
| workOffsetValue | : LIST [1:N] OF REAL, | Read only; |
| workOffsetRotation | : LIST [1:N] OF REAL, | Read only; |
| workOffsetScalingFactor | : LIST [1:N] OF REAL, | Read only; |
| workOffsetMirroringEnabled | : LIST [1:N] OF BOOLEAN, | Read only; |

- 구성 데이터 설명

- workOffsetIndex 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드를 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetIndex?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.

| SIEMENS | KCNC |
| ------------ | ------- |
| 0 : G500 | |
| 1 : G54 | 1 : G54 |
| 2 : G55 | 2 : G55 |
| 3 : G56 | 3 : G56 |
| 4 : G57 | 4 : G57 |
| 5 : G505 | 5 : G58 |
| 6 : G506 | 6 : G59 |
| : | |
| : | |
| n : G(500+n) | |
| : | |
| 99: G599 | |

- workOffsetCode 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetCode?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- workOffsetValue 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드에 대한 축별 총 오프셋량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetValue 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetValue=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetValue?machine=i&channel=j&workOffsetValue=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetRotation (SIEMENS only) 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드에 대한 축별 총 오프셋 회전량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetRotation 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetRotation=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetRotation?machine=i&channel=j&workOffsetRotation=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetScalingFactor (SIEMENS only) 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드에 대한 축별 총 오프셋 확장량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetScalingFactor 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetScalingFactor=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetScalingFactor?machine=i&channel=j&workOffsetScalingFactor=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetMirroringEnabled (SIEMENS only) 실행 중인 NC 프로그램에서 사용하고 있는 공작물 좌표계의 G 코드에 대한 축별 총 오프셋 미러링 여부의 리스트를 나타내는 논리형 속성입니다. "Filter" 로 workOffsetMirroringEnabled 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetMirroringEnabled=1)

data://machine/channel/currentProgram/currentTotalWorkOffset/workOffsetMirroringEnabled?machine=i&channel=j&workOffsetMirroringEnabled=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 축인지를 의미하는 정수값입니다. 

---

## E. currentFile
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 currentFile 데이터는 실행 중인 NC 프로그램에 대한 파일 정보를 나타내며, 프로그램에 대한 식별자, 프로그램의 저장 경로 등을 포함합니다.

- 데이터 구성

| currentFile | | |
| ------------------- | --------- | ---------- |
| programName | : STRING, | Read-only; |
| programPath | : STRING, | Read-only; |
| programSize | : REAL, | Read-only; |
| programDate | : STRING, | Read-only; |
| programNameWithPath | : STRING, | Read-only; |

- 구성 데이터 설명

- programName 실행 중인 NC 프로그램의 식별자로서, NC 프로그램의 파일명을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentFile/programName?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programPath 실행 중인 NC 프로그램이 저장되어 있는 디렉토리 혹은 폴더, 드라이브의 경로를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentFile/programPath?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programSize 실행 중인 NC 프로그램의 파일 크기를 나타내는 실수형 속성입니다. (단위 : byte)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentFile/programSize?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programDate 실행 중인 NC 프로그램의 생성 날짜에 대한 연, 월, 일, 시, 분, 초 정보를 나타내는 문자열 속성입니다. (형식 : yyyy-MM-ddTHH:mm:ss)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentFile/programDate?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programNameWithPath 실행 중인 NC 프로그램의 파일명을 디렉토리 혹은 폴더, 드라이브 경로와 함께 표현한 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/currentFile/programNameWithPath?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. 

---

## F. mainFile
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 mainFile 데이터는 실행 중인 NC 프로그램과는 별개로, 현재 선택되어 있는 NC 프로그램에 대한 파일 정보를 나타내며, 프로그램에 대한 식별자, 프로그램의 저장 경로 등을 포함합니다.

- 데이터 구성

| mainFile | | |
| ------------------- | --------- | ---------- |
| programName | : STRING, | Read-only; |
| programPath | : STRING, | Read-only; |
| programSize | : REAL, | Read-only; |
| programDate | : STRING, | Read-only; |
| programNameWithPath | : STRING, | Read-only; |

- 구성 데이터 설명

- programName 선택 중인 NC 프로그램의 식별자로서, NC 프로그램의 파일명을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/mainFile/programName?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programPath 선택 중인 NC 프로그램이 저장되어 있는 디렉토리 혹은 폴더, 드라이브의 경로를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/mainFile/programPath?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programSize 선택 중인 NC 프로그램의 파일 크기를 나타내는 실수형 속성입니다. (단위 : byte)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/mainFile/programSize?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programDate 선택 중인 NC 프로그램의 생성 날짜에 대한 연, 월, 일, 시, 분, 초 정보를 나타내는 문자열 속성입니다. (형식 : yyyy-MM-ddTHH:mm:ss)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/mainFile/programDate?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- programNameWithPath 선택 중인 NC 프로그램의 파일명을 디렉토리 혹은 폴더, 드라이브 경로와 함께 표현한 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/mainFile/programNameWithPath?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. 

---

## G. controlOption
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 5.2.1.2.5 currentProgram 

- 개요 controlOption 데이터는 실행 중인 NC 프로그램의 제어 환경에 대한 정보를 나타내며 singleBlock, dryRun, optionalStop, blockSkip, machineLock 기능을 포함합니다.

- 데이터 구성

| controlOption | | |
| ------------- | ------------------------ | ---------- |
| singleBlock | : BOOLEAN, | Read-only; |
| dryRun | : BOOLEAN, | Read-only; |
| optionalStop | : BOOLEAN, | Read-only; |
| blockSkip | : LIST [1:N] OF BOOLEAN, | Read-only; |
| machineLock | : BOOLEAN, | Read-only; |

- 구성 데이터 설명

- singleBlock NC 프로그램 실행 시, 한 블럭의 실행이 종료될 때마다 자동운전이 정지되도록 하는 기능에 대한 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/controlOption/singleBlock?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- dryRun NC 프로그램 실행 시, 수동으로 지정한 이송속도로 움직이도록 하는 기능에 대한 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/controlOption/dryRun?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- optionalStop NC 프로그램 실행 시, M01 명령을 이용하여 선택적으로 정지할 수 있도록 하는 기능에 대한 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/controlOption/optionalStop?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- blockSkip NC 프로그램 실행 시, ‘/’로 시작하는 블록을 실행하지 않고 건너뛸 수 있도록 하는 기능에 대한 활성화 여부의 리스트를 나타내는 논리형 속성입니다. "Filter" 로 blockSkip 을 사용하여 리스트 내 개체를 식별합니다. (예: blockSkip=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/controlOption/blockSkip?machine=i&channel=j&blockSkip=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 블락인지를 의미하는 정수값입니다.
- machineLock 축을 이송하지 않고 NC 프로그램을 실행시키는 기능에 대한 활성화 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/currentProgram/controlOption/machineLock?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.6 workOffset
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요
- workOffset 데이터는 계통 내 공작물 좌표계 관련 G 코드에 대한 오프셋량 정보를 나타내며, G 코드 인덱스, 축별 오프셋 량 리스트, 축별 오프셋 회전량 리스트, 축별 오프셋 확장량 리스트, 축별 오프셋 미러링 여부 리스트를 포함합니다. 각 NC에서 이용 가능한 공작물 관련 G코드 인덱스는 다음 표와 같습니다.

| FANUC | SIEMENS | MITSUBISHI | KCNC |
| --------------- | ------------ | ---------- | ------- |
| 0 : EXT | 0 : G500 | 0 : EXT | |
| 1 : G54 | 1 : G54 | 1 : G54 | 1 : G54 |
| 2 : G55 | 2 : G55 | 2 : G55 | 2 : G55 |
| 3 : G56 | 3 : G56 | 3 : G56 | 3 : G56 |
| 4 : G57 | 4 : G57 | 4 : G57 | 4 : G57 |
| 5 : G58 | 5 : G505 | 5 : G58 | 5 : G58 |
| 6 : G59 | 6 : G506 | 6 : G59 | 6 : G59 |
| 7 : G54.1P1 | : | | |
| : | : | | |
| n : G54.1P(n-6) | n : G(500+n) | | |
| : | : | | |
| 306 : G54.1P300 | 99 : G599 | | |

- 데이터 구성

| workOffset | | |
| -------------------------- | ------------------------ | ----------- |
| workOffsetValue | : LIST [1:N] OF REAL, | Read/Write; |
| workOffsetRotation | : LIST [1:N] OF REAL, | Read/Write; |
| workOffsetScalingFactor | : LIST [1:N] OF REAL, | Read/Write; |
| workOffsetMirroringEnabled | : LIST [1:N] OF BOOLEAN, | Read/Write; |
| workOffsetFine | : LIST [1:N] OF REAL, | Read/Write; |

- 구성 데이터 설명

- workOffsetValue 해당 계통에서 G 코드 인덱스에 대한 축별 오프셋량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetValue 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetValue=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/workOffset/workOffsetValue?machine=i&channel=j&workOffset=k&workOffsetValue=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 G 코드 인덱스인지를 의미하는 정수값입니다. l 은 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetRotation (SIEMENS only) 해당 계통에서 G 코드 인덱스에 대한 축별 오프셋 회전량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetRotation 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetRotation=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/workOffset/workOffsetRotation?machine=i&channel=j&workOffset=k&workOffsetRotation=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 G 코드 인덱스인지를 의미하는 정수값입니다. l 은 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetScalingFactor (SIEMENS only) 해당 계통에서 G 코드 인덱스에 대한 축별 오프셋 확장량의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetScalingFactor 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetScalingFactor=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/workOffset/workOffsetScalingFactor?machine=i&channel=j&workOffset=k&workOffsetScalingFactor=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 G 코드 인덱스인지를 의미하는 정수값입니다. l 은 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetMirroringEnabled (SIEMENS only) 해당 계통에서 G 코드 인덱스에 대한 축별 오프셋량 미러링 여부의 리스트를 나타내는 논리형 속성입니다. "Filter" 로 workOffsetMirroringEnabled 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetMirroringEnabled=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/workOffset/workOffsetMirroringEnabled?machine=i&channel=j&workOffset=k&workOffsetMirroringEnabled=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 G 코드 인덱스인지를 의미하는 정수값입니다. l 은 몇 번째 축인지를 의미하는 정수값입니다.
- workOffsetFine (SIEMENS only) 해당 계통에서 G 코드 인덱스에 대한 축별 오프셋 Fine의 리스트를 나타내는 실수형 속성입니다. "Filter" 로 workOffsetFine 을 사용하여 리스트 내 개체를 식별합니다. (예: workOffsetFine=1)

주소 표기는 다음과 같이 합니다. data://machine/channel/workOffset/workOffsetFine?machine=i&channel=j&workOffset=k&workOffsetFine=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 G 코드 인덱스인지를 의미하는 정수값입니다. l 은 몇 번째 축인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.7 alarm
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 alarm 데이터는 해당 채널에서 발생한 알람에 대한 정보를 나타내며 알람 발생 여부, 알람 번호, 알람 메시지 등을 포함합니다.

- 데이터 구성

| alarm | | |
| --------------- | ----------------------------- | ---------- |
| alarm | : LIST [1:N] OF STRING(JSON), | Read-only; |
| alarmText | : STRING, | Read-only; |
| alarmCategory | : STRING, | Read-only; |
| alarmNumber | : STRING, | Read-only; |
| raisedTimeStamp | : STRING, | Read-only; |

- 구성 데이터 설명

- alarm 해당 계통에서 발생한 모든 알람에 대한 Text, Category, Number, raisedTimeStamp를 리스트로 나타내는 문자열(JSON 형태) 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarm?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- alarmText 해당 계통에서 발생한 알람에 대한 상세한 설명을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarm/alarmText?machine=i&channel=j&alarm=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 알람인지를 의미하는 정수값입니다.
- alarmCategory 해당 계통에서 발생한 알람의 유형에 대한 정보를 표현하는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarm/alarmCategory?machine=i&channel=j&alarm=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 알람인지를 의미하는 정수값입니다.
- alarmNumber 해당 계통에서 발생한 알람의 종류에 대한 번호를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarm/alarmNumber?machine=i&channel=j&alarm=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 알람인지를 의미하는 정수값입니다.
- raisedTimeStamp 해당 계통에서 발생한 알람의 발생 시간 정보를 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/alarm/raisedTimeStamp?machine=i&channel=j&alarm=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번째 알람인지를 의미하는 정수값입니다. 

---

##### 5.2.1.2.8 variable
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.2 channel 

- 개요 variable 데이터는 해당 계통에서 사용하는 변수에 대한 정보를 나타냅니다.

- 데이터 구성

| variable | | |
| ------------ | ------- | ----------- |
| userVariable | : REAL, | Read/Write; |

- 구성 데이터 설명

- userVariable 해당 계통에서 사용하는 사용자 변수입니다.

주소 표기는 다음과 같이 합니다. data://machine/channel/variable/userVariable?machine=i&channel=j&variable=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. k 는 몇 번 사용자 변수인지를 의미하는 정수값입니다. 

---

##### 5.2.1.3 plc
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 

- 개요 plc 데이터는 각 이기종 CNC 내부의 PLC(NC internal PLC) 데이터 정보를 나타내기 위한 공용화 데이터 모델로써, 다양한 데이터 타입에 대응하도록 구성되어 있습니다.
전체 데이터 구성은 아래 그림과 같습니다.

![image](./lib/NewItem%201.png)
TORUS Platform이 지원하는 CNC 내부 PLC (NC internal PLC)의 memory는 위 그림과 같이, 10개의 memory block으로 구성됩니다.
- 데이터 구성

| plc | | | |
| --- | ----------- | --------------------------------- | ----------- |
| | memory | | |
| | rbitBlock | : LIST [1:65536] OF BOOLEAN, | Read-only; |
| | bitBlock | : LIST [1:65536] OF BOOLEAN, | Read/Write; |
| | rbyteBlock | : LIST [1:65536] OF byte, | Read-only; |
| | byteBlock | : LIST [1:65536] OF byte, | Read/Write; |
| | rwordBlock | : LIST [1:65536] OF word(2byte), | Read-only; |
| | wordBlock | : LIST [1:65536] OF word(2byte), | Read/Write; |
| | rdwordBlock | : LIST [1:65536] OF dword(4byte), | Read-only; |
| | dwordBlock | : LIST [1:65536] OF dword(4byte), | Read/Write; |
| | rqwordBlock | : LIST [1:65536] OF qword(8byte), | Read-only; |
| | qwordBlock | : LIST [1:65536] OF qword(8byte), | Read/Write; |

- 구성 데이터 설명

- rbitBlock 읽기 전용 bit type 데이터 블록입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | ---------------- | ----------------- | --------------------- |
| 1 | 1bit | 1~65536 | 1 byte Data type | ~ 65536 bit (8kB) | input type, read-only |

이 데이터 블록에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - KCNC/CSCAM : BIT TYPE - MITSUBISHI : BIT TYPE - SIEMENS : BIT TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rbitBlock?machine=i&rbitBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 rbitBlock의 어드레스를 의미하는 정수값입니다. "rbitBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, rbitBlock100번부터 rbitBlock200번까지의 범위를 의미합니다.
- bitBlock 읽기/쓰기가 가능한 bit type 데이터 블록입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | ----------------- | --- |
| 2 | 1bit | 1~65536 | boolean | ~ 65536 bit (8kB) | |

이 데이터 블록에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - KCNC/CSCAM : BIT TYPE - MITSUBISHI : BIT TYPE - SIEMENS : BIT TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/bitBlock?machine=i&bitBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 bitBlock의 어드레스를 의미하는 정수값입니다. "bitBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, bitBlock100번부터 bitBlock200번까지의 범위를 의미합니다.
- rbyteBlock 읽기 전용 byte type 데이터 블록입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | ------------------ | --------------------- |
| 3 | 1byte | 1~65536 | 1 byte Data | ~ 65536 bit (64kB) | input type, read-only |

이 데이터 블록에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : BYTE TYPE - SIEMENS : BYTE TYPE - MITSUBISHI : BYTE TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rbyteBlock?machine=i&rbyteBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 rbyteBlock의 어드레스를 의미하는 정수값입니다. "rbyteBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, rbyteBlock100번부터 rbyteBlock200번까지의 범위를 의미합니다.
- byteBlock 읽기/쓰기가 가능한 byte type 데이터 블럭입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | ------------------- | --- |
| 4 | 1byte | 1~65536 | 1 byte Data | ~ 65536 byte (64kB) | |

이 데이터 블록에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : BYTE TYPE - SIEMENS : BYTE TYPE - MITSUBISHI : BYTE TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/byteBlock?machine=i&byteBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 byteBlock의 어드레스를 의미하는 정수값입니다. "byteBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, byteBlock100번부터 byteBlock200번까지의 범위를 의미합니다.
- rwordBlock 읽기 전용 word type 데이터 블럭입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --------------------- |
| 5 | 2byte | 1~65536 | 2 byte Data | ~ 131072 byte (128kB) | input type, read-only |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC: WORD TYPE - SIEMENS : WORD TYPE - MITSUBISHI : WORD TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rwordBlock?machine=i&rwordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 rwordBlock의 어드레스를 의미하는 정수값입니다. "rwordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, rwordBlock100번부터 rwordBlock200번까지의 범위를 의미합니다.
- wordBlock 읽기/쓰기가 가능한 word type 데이터 블럭입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --- |
| 6 | 2byte | 1~65536 | 2 byte Data | ~ 131072 byte (128kB) | |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC: WORD TYPE - SIEMENS : WORD TYPE - MITSUBISHI : WORD TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/wordBlock?machine=i&wordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 wordBlock의 어드레스를 의미하는 정수값입니다. "wordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, wordBlock100번부터 wordBlock200번까지의 범위를 의미합니다.
- rdwordBlock 읽기 전용 double word type 데이터 블럽입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --------------------- |
| 7 | 4 byte | 1~65536 | 4 byte Data | ~ 262144 byte (256kB) | input type, read-only |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : LONG TYPE, FLOATING32 TYPE - SIEMENS : DWORD TYPE - KCNC/CSCAM : LONG TYPE - MITSUBISHI : DWORD TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rdwordBlock?machine=i&rdwordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 rdwordBlock의 어드레스를 의미하는 정수값입니다. "rdwordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, rdwordBlock100번부터 rdwordBlock200번까지의 범위를 의미합니다.
- dwordBlock 읽기.쓰기가 가능한 dwordBlock type 데이터 블럭입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --- |
| 8 | 4 byte | 1~65536 | 4 byte Data | ~ 262144 byte (256kB) | |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : LONG TYPE, FLOATING32 TYPE - SIEMENS : DWORD TYPE - KCNC/CSCAM : LONG TYPE - MITSUBISHI : DWORD TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rdwordBlock?machine=i&dwordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 dwordBlock의 어드레스를 의미하는 정수값입니다. "dwordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, dwordBlock100번부터 dwordBlock200번까지의 범위를 의미합니다.
- rqwordBlock 읽기 전용 quad-word type 데이터 블럭립니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --------------------- |
| 9 | 8 byte | 1~65536 | 8 byte Data | ~ 524288 byte (512kB) | input type, read-only |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : FLOATING64 TYPE - KCNC/CSCAM : DOUBLE TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/rqwordBlock?machine=i&rqwordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 rqwordBlock의 어드레스를 의미하는 정수값입니다. "rqwordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, rqwordBlock100번부터 rqwordBlock200번까지의 범위를 의미합니다.
- qwordBlock 읽기/쓰기가 가능한 quad-word type 데이터 블럭입니다.

| Memory Block type number | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------- | ---------- | --------------- | --------------------- | --- |
| 10 | 8 byte | 1~65536 | 8 byte Data | ~ 524288 byte (512kB) | |

이 데이터 블럭에 할당 가능한 CNC 데이터 타입은 다음과 같습니다. - FANUC : FLOATING64 TYPE - KCNC/CSCAM : DOUBLE TYPE 주소 표기는 다음과 같이 합니다. data://machine/plc/memory/qwordBlock?machine=i&qwordBlock=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. "machine=1-2"와 같이 범위를 지정해도 됩니다. 위 예와 같은 경우, machine ID 1번 장비부터 machine ID 2번 장비까지를 의미합니다. j 는 qwordBlock의 어드레스를 의미하는 정수값입니다. "qwordBlock=100-200"와 같이, 범위를 지정해도 됩니다. 위 예와 같은 경우, qwordBlock100번부터 qwordBlock200번까지의 범위를 의미합니다.
- 기타 유의 사항 NC internal PLC 데이터를 읽고 쓰기 위해서 getData, updateData 함수를 사용해야 합니다. NC internal PLC 데이터는 기존의 getPlcSignal, setPlcSignal 함수를 사용할 수 없습니다. 추후, getPlcSignal 함수와 setPlcSignal 함수는 지원이 중단될 수 있습니다.

---

##### 5.2.1.4 toolArea
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 

- 개요 toolArea 데이터는 장비 내 계통에서 참조할 수 있는 공구 영역에 대한 정보를 나타내며, 공구 영역의 식별자 정보와 함께 사용 가능 여부, 현재 공구 영역 내에 존재하는 매거진 및 공구에 대한 정보들을 포함합니다. SIEMENS의 경우 공구를 매거진에 탑재하지 않고 등록만 하는 것도 가능하기 때문에 각 경우에 대한 개수를 나타내는 정보들도 포함합니다.

- 데이터 구성

| toolArea | | |
| ----------------------- | --------------------------- | ---------- |
| toolAreaEnabled | : BOOLEAN, | Read-only; |
| numberOfMagazines | : INTEGER, | Read-only; |
| numberOfRegisteredTools | : INTEGER, | Read-only; |
| numberOfLoadedTools | : INTEGER, | Read-only; |
| numberOfToolGroups | : INTEGER, | Read-only; |
| numberOfToolOffsets | : INTEGER, | Read-only; |
| magazine | : LIST [1:N] OF "magazine"; | |
| tools | : LIST [1:N] OF "tools"; | |

- 구성 데이터 설명

- toolAreaEnabled 해당 공구 영역의 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/toolAreaEnabled?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- numberOfMagazines 해당 공구 영역에서 사용 가능한 매거진의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/numberOfMagazines?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- numberOfRegisteredTools 해당 공구 영역에 등록된 공구의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/numberOfRegisteredTools?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- numberOfLoadedTools 해당 공구 영역에 등록된 공구 중 매거진에 탑재된 공구의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/numberOfLoadedTools?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- numberOfToolGroups 해당 공구 영역에 등록된 공구 그룹의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/numberOfToolGroups?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- numberOfToolOffsets 해당 공구 영역에 등록된 공구 오프셋의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/numberOfToolOffsets?machine=i&toolArea=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다.
- magazine 해당 공구 영역에 등록된 매거진의 리스트를 나타내며, 각 매거진은 magazine 타입으로 정의됩니다. "Filter" 로 magazine 을 사용하여 리스트 내 개체를 식별합니다. (예: magazine=1) 자세한 설명은 " 5 .2.1.4.1 magazine " 절에서 확인할 수 있습니다.
- tools 해당 공구 영역에 등록된 공구의 리스트를 나타내며, 각 공구는 tools 타입으로 정의됩니다. "Filter" 로 tools 을 사용하여 리스트 내 개체를 식별합니다. (예: tools=1) 자세한 설명은 " 5 .2.1.4.2 activeTool/tools " 절에서 확인할 수 있습니다.

---

##### 5.2.1.4.1 magazine
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.4 toolArea 

- 개요 magazine 데이터는 NC에서 사용할 공구가 탑재된 매거진과 관련된 정보를 나타내며, 매거진의 식별자, 매거진 내 위치한 공구 정보 등을 포함합니다.

- 데이터 구성

| magazine | | |
| ---------------------- | ---------- | ---------- |
| magazineEnabled | : BOOLEAN, | Read-only; |
| magazineName | : STRING, | Read-only; |
| numberOfRealLocations | : INTEGER, | Read-only; |
| magazinePhysicalNumber | : INTEGER, | Read-only; |
| numberOfLoadedTools | : INTEGER, | Read-only; |

- 구성 데이터 설명

- magazineEnabled 해당 매거진의 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/magazine/magazineEnabled?machine=i&toolArea=j&magazine=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 매거진인지를 의미하는 정수값입니다.
- magazineName (SIEMENS only) 해당 매거진의 이름을 나타내는 고유의 문자열로 표현됩니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/magazine/magazineName?machine=i&toolArea=j&magazine=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 매거진인지를 의미하는 정수값입니다.
- numberOfRealLocations 해당 매거진에 공구 탑재가 가능한 물리적 위치의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/magazine/numberOfRealLocations?machine=i&toolArea=j&magazine=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 매거진인지를 의미하는 정수값입니다.
- magazinePhysicalNumber 해당 매거진에 할당된 물리적 번호를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/magazine/magazinePhysicalNumber?machine=i&toolArea=j&magazine=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 매거진인지를 의미하는 정수값입니다.
- numberOfLoadedTools 해당 매거진에 탑재된 공구의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/toolArea/magazine/numberOfLoadedTools?machine=i&toolArea=j&magazine=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 매거진인지를 의미하는 정수값입니다. 

---

##### 5.2.1.4.2 activeTool/tools
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.4 toolArea 

- 개요 Tool 데이터는 공구 정보를 나타내는 것으로 공구에 대한 식별자, 기하학적 사양 등을 포함합니다. activeTool, installTools, registerTools 형태로 나뉘며 activeTool은 현재 선택되어 활성화 되어 있는 공구 정보를, installTools는 지정된 공구 번호를 사용해서 해당 공구 정보를 나타냅니다. registerTools는 실제 NC 상에 매거진 장착 공구로 설정된 공구들의 정보를 가지고 있으며, 이를 지정하기 위해 NC에 설정된 순서에 따른 인덱스 번호를 사용합니다.

- 데이터 구성

| activeTool | | |
| ------------------ | ------------------------ | ---------- |
| locationNumber | : INTEGER, | Read-only |
| toolName | : STRING, | Read-only; |
| toolNumber | : INTEGER, | Read-only; |
| numberOfEdges | : INTEGER, | Read-only; |
| toolEnabled | : INTEGER, | Read-only; |
| magazineNumber | : INTEGER, | Read-only; |
| sisterToolNumber | : INTEGER, | Read-only; |
| toolLifeUnit | : INTEGER, | Read-only; |
| toolGroupNumber | : LIST [1:N] OF INTEGER, | Read-only; |
| toolUseOrderNumber | : INTEGER, | Read-only; |
| toolStatus | : INTEGER, | Read-only; |
| toolEdge | : toolEdge; | |

| installTools, registerTools | | |
| --------------------------- | --------------------------- | ----------- |
| locationNumber | : INTEGER, | Read-only; |
| toolName | : STRING, | Read/Write; |
| toolNumber | : INTEGER; | |
| numberOfEdges | : INTEGER, | Read-only; |
| toolEnabled | : INTEGER, | Read/Write; |
| magazineNumber | : INTEGER, | Read-only; |
| sisterToolNumber | : INTEGER, | Read/Write; |
| toolLifeUnit | : INTEGER, | Read/Write; |
| toolGroupNumber | : LIST [1:N] OF INTEGER, | Read-only; |
| toolUseOrderNumber | : INTEGER, | Read-only; |
| toolStatus | : INTEGER, | Read/Write; |
| toolEdge | : LIST [1:N] OF “toolEdge”; | |

- 구성 데이터 설명

- locationNumber 해당 공구가 매거진 내 탑재된 위치를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/locationNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/locationNumber?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/locationNumber?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다.
- toolName 해당 공구의 이름을 나타내는 문자열 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolName?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolName?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolName?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 매거진에 장착된 몇 번째 공구인지를 의미하는 인덱스 번호로 정수값입니다.
- toolNumber 해당 공구의 식별자로서, 공구 번호를 나타내는 정수형 속성입니다. activeTool의 공구 번호를 나타내며, installTools, registerTools에서는 인덱스 속성이므로 데이터의 읽고 쓰기가 불가능합니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- numberOfEdges 해당 공구에 대한 공구 날의 총 개수를 나타내는 정수형 속성으로, 기본 값으로 1이 설정됩니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/numberOfEdges?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/numberOfEdges?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/numberOfEdges?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다.
- toolEnabled 해당 공구의 공구 영역 등록 및 매거진 탑재 여부를 나타내며, 각 경우에 대한 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEnabled?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEnabled?machine=i&toolArea=j&tools=k&toolGroupNumber=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEnabled?machine=i&toolArea=j®isterTools=k&toolGroupNumber=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.

| 결과 |
| ------------------------ |
| 0: 공구 영역 미등록, 매거진 미탑재 상태 |
| 1: 공구 영역 등록, 매거진 미탑재 상태 |
| 2: 공구 영역 등록, 매거진 탑재 상태 |

- magazineNumber 해당 공구가 탑재된 매거진의 번호를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/magazineNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/magazineNumber?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/magazineNumber?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다.
- sisterToolNumber 해당 공구에 할당된 대체 공구 번호를 나타내는 정수형 속성입니다. SIEMENS에서는 현재 사용 중인 공구의 수명이 다하였을 때 대체하여 사용할 공구들에게 오름차순으로 해당 번호를 할당합니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/sisterToolNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/sisterToolNumber?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/sisterToolNumber?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다.
- toolLifeUnit 해당 공구의 공구 수명을 측정하는 단위 기준을 나타내며, 각 NC에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolLifeUnit?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolLifeUnit?machine=i&toolArea=j&tools=k&toolLifeUnit=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolLifeUnit?machine=i&toolArea=j®isterTools=k&toolLifeUnit=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| ------------- | ----- | ---------------------------------------------------------- | ----- | ---------- | ---- |
| 0 : no unit | O | O | O | | O |
| 1 : time | O | O (tool life monitoring) | | O | |
| 2 : count | O | O (no. of workpieces monitoring) | | | |
| - | | | | | |
| 4 : wear | | O (monitoring of edge wear parameters using wear limit) | | | |
| 5 : count(장착) | | | | O | |
| 6 : count(사용) | | | | O | |
| - | | | | | |
| 8 : offset | | O (monitoring of total offset parameters using wear limit) | | | |

- toolGroupNumber 해당 공구가 참조된 공구 그룹 번호의 리스트를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolGroupNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolGroupNumber?machine=i&toolArea=j&tools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolGroupNumber?machine=i&toolArea=j®isterTools=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다.
- toolUseOrderNumber (FANUC only) 해당 공구가 참조된 공구 그룹 내에서의 공구 사용 순서를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolUseOrderNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolUseOrderNumber?machine=i&toolArea=j&tools=k&toolUseOrderNumber=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolUseOrderNumber?machine=i&toolArea=j®isterTools=k&toolUseOrderNumber=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- toolStatus 해당 공구의 사용 상태를 나타내며, 각 NC 에서 이용가능한 값들과 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolStatus?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolStatus?machine=i&toolArea=j&tools=k&toolStatus=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolStatus?machine=i&toolArea=j®isterTools=k&toolStatus=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. ※ SIEMENS는 Tool Status의 값이 합쳐져서 출력됩니다. 예를 들어 131이 출력되면 1 + 2 + 128 = 131 (1:Active tool, 2:Enabled, 128:Tool was in use) 3가지 상태가 적용된 것입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| --------------------------------------------------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : Not enabled | | O | O | | O |
| 1 : Active tool | | O | O | O | O |
| 2 : Enabled | | O | O | | O |
| 4 : Disabled | | O | | | |
| 8 : Measured | | O | | | |
| 9: 미사용 공구 | | | | O | |
| 10 : 정상 수명 공구 | | | | O | |
| 11 : Tool data is available (using) | O | | | | |
| 12 : This tool is registered (available) | O | | | | |
| 13 : This tool has expired | O | | | | |
| 14 : This tool was skipped | O | | | | |
| 16 : Prewarning limit reached | | O | | | |
| 32 : Tool being changed | | O | | | |
| 64 : Fixed location coded | | O | | | |
| 128 : Tool was in use | | O | | | |
| 256 : Tool is in the buffer magazine with transport order | | O | | | |
| 512 : Ignore disabled state of tool | | O | | | |
| 1024 : Tool must be unloaded | | O | | | |
| 2048 : Tool must be loaded | | O | | | |
| 4096 : Tool is a master tool | | O | | | |
| 8192 : Reserved | | O | | | |
| 16384 : Tool is marked for 1:1 exchange | | O | | | |
| 32768 : Tool is being used as a manual tool | | O | | | |

- toolEdge 공구 날을 나타내는 것으로 toolEdge 타입으로 정의됩니다. activeTool에서는 현재 선택되어 활성화된 공구에서 사용 가능한 공구 날을 나타냅니다. installTools와 registerTools에서는 해당 공구에서 사용 가능한 공구 날의 리스트를 나타며, "Filter"로 toolEdge 를 사용하여 리스트 내 개체를 식별합니다. (예 : tooledge=1) 자세한 설명은 ' 5.2.1.4.2:A. toolEdge' 절에서 확인할 수 있습니다.

---

## A. toolEdge
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.4 toolArea 5.2.1.4.2 activeTool/tools 

- 개요 toolEdge 데이터는 해당 공구에 대한 공구 날 정보를 나타내며, 공구날 번호, 공구의 유형, 공구의 길이 및 직경, 공구 수명 등을 포함합니다. activeTool, installTools, registerTools 형태로 나뉘며 activeTool의 toolEdge는 현재 선택되어 활성화 되어 있는 공구에 대한 공구 날 정보를, installTools의 toolEdge는 지정된 공구 번호의 해당 공구에 대한 공구 날 정보를 나타냅니다. registerTools의 toolEdge는 NC에 설정된 순서에 따른 공구 인덱스 번호의 해당 공구에 대한 공구 날 정보를 나타냅니다. 공구 유형에 따라 사용 가능한 형상 정보가 다릅니다. 각 NC 의 공구 유형에 따라 사용 가능한 형상 정보는 다음 표와 같습니다.
[FANUC 공구 유형에 따른 공구 형상 정보]

| | geo/wearLengthOffset | geo/wearLengthOffsetZ | geo/wearRadiusOffset | cuttingEdgePosition | holderAngle | tipAngle | insertAngle |
| ----------------------------- | -------------------- | --------------------- | -------------------- | ------------------- | ----------- | -------- | ----------- |
| 10 (General-purpose tool) | √ | √ | √ | √ | √ | √ | √ |
| 11 (Threading tool) | √ | √ | √ | √ | - | √ | √ |
| 12 (Grooving tool) | √ | √ | √ | √ | - | - | - |
| 13 (Round-nose tool) | √ | √ | √ | √ | - | - | - |
| 14 (Point nose straight tool) | √ | √ | √ | √ | √ | √ | √ |
| 15 (Versatile tool) | √ | √ | √ | √ | - | - | - |
| 20 (Drill) | √ | √ | √ | √ | - | √ | √ |
| 21 (Counter sink tool) | √ | √ | √ | √ | - | - | - |
| 22 (Flat end mill)) | √ | √ | √ | √ | - | - | - |
| 23 (Ball end mill) | √ | √ | √ | √ | - | - | - |
| 24 (Tap) | √ | √ | √ | √ | - | - | - |
| 25 (Reamer) | √ | √ | √ | √ | - | - | - |
| 26 (Boring tool) | √ | √ | √ | √ | - | - | - |
| 27 (Face mill) | √ | √ | √ | √ | - | - | - |

[SIEMENS 공구 유형에 따른 공구 형상 정보]

| | geo/wear LengthOffset | geo/wear LengthOffsetZ | geo/wear RadiusOffset | referenceDirection HolderAngle | number OfTeeth | holder Angle | insert Width | tip Angle | insert Angle | insert Length | cutting EdgePosition |
| ------------------------------ | --------------------- | ---------------------- | --------------------- | ------------------------------ | -------------- | ------------ | ------------ | --------- | ------------ | ------------- | -------------------- |
| 100 (Milling Tool) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 110 (Ball nose end mill) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 111 (Conical ball end) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 120 (End mill) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 121 (End mill corner rounding) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 130 (Angle head cutter) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 131 (Corn.round.and.hd.cut) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 140 (Facing tool) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 145 (Thread cutter) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 150 (Side mill) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 151 (Saw) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 155 (Bevelled cutter) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 156 (Bevelled cutter corner) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 157 (Tap. Die-sink. cutter) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 160 (Drill&thread cut.) | √ | √ | √ | - | √ | - | - | - | - | - | √ |
| 200 (Twist drill) | √ | √ | √ | - | - | - | - | √ | - | - | √ |
| 205 (Solid drill) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 210 (Boring bar) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 220 (Center drill) | √ | √ | √ | - | - | - | - | √ | - | - | √ |
| 230 (Countersink) | √ | √ | √ | - | - | - | - | √ | - | - | √ |
| 231 (Counterbore) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 240 (Tap) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 241 (Fine tap) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 242 (Tap, Whitworth) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 250 (Reamer) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 500 (Roughing tool) | √ | √ | √ | √ | - | √ | - | - | √ | √ | √ |
| 510 (Finishing tool) | √ | √ | √ | √ | - | √ | - | - | √ | √ | √ |
| 520 (Plunge cutter) | √ | √ | √ | - | - | - | √ | - | - | √ | √ |
| 530 (Cutting tool) | √ | √ | √ | - | - | - | √ | - | - | √ | √ |
| 540 (Threading tool) | √ | √ | √ | - | - | - | - | - | - | √ | √ |
| 550 (Button tool) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 560 (Rotary Drill) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 580 (3D turning probe) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 585 (Calibrating tool) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 700 (Slotting saw) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 710 (3D probe) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 711 (Edge finder) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 712 (Mono probe) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 713 (L probe) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 714 (Star probe) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 725 (Calibrating tool) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 730 (Stop) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 731 (Mandrel) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 732 (Steady rest) | √ | √ | √ | - | - | - | - | - | - | - | √ |
| 900 (Auxiliary tools) | √ | √ | √ | - | - | - | - | - | - | - | √ |

- 데이터 구성

| activateTool의 toolEdge | | |
| ----------------------------- | ---------- | ---------- |
| edgeNumber | : INTEGER, | Read-only; |
| toolType | : INTEGER, | Read-only; |
| lengthOffsetNumber | : INTEGER, | Read-only; |
| geoLengthOffset | : REAL, | Read-only; |
| wearLengthOffset | : REAL, | Read-only; |
| radiusOffsetNumber | : INTEGER, | Read-only; |
| geoRadiusOffset | : REAL, | Read-only; |
| wearRadiusOffset | : REAL, | Read-only; |
| edgeEnabled | : BOOLEAN; | Read-only; |
| geoLengthOffsetZ | : REAL, | Read-only; |
| wearLengthOffsetZ | : REAL, | Read-only; |
| geoLengthOffsetY | : REAL, | Read-only; |
| wearLengthOffsetY | : REAL, | Read-only; |
| geoOffsetNumber | : INTEGER, | Read-only; |
| wearOffsetNumber | : INTEGER, | Read-only; |
| cuttingEdgePosition | : INTEGER, | Read-only; |
| tipAngle | : REAL, | Read-only; |
| holderAngle | : REAL, | Read-only; |
| insertAngle | : REAL, | Read-only; |
| insertWidth | : REAL, | Read-only; |
| insertLength | : REAL, | Read-only; |
| referenceDirectionHolderAngle | : REAL, | Read-only; |
| directionOfSpindleRotation | : INTEGER, | Read-only; |
| numberOfTeeth | : INTEGER, | Read-only; |
| toolLife | : toolLife | |

| installTool와 registerTools의 toolEdge | | |
| ------------------------------------ | ---------- | ----------- |
| edgeNumber | : INTEGER, | |
| toolType | : INTEGER, | Read/Write; |
| lengthOffsetNumber | : INTEGER, | Read/Write; |
| geoLengthOffset | : REAL, | Read/Write; |
| wearLengthOffset | : REAL, | Read/Write; |
| radiusOffsetNumber | : INTEGER, | Read/Write; |
| geoRadiusOffset | : REAL, | Read/Write; |
| wearRadiusOffset | : REAL, | Read/Write; |
| edgeEnabled | : BOOLEAN; | Read-only; |
| geoLengthOffsetZ | : REAL, | Read/Write; |
| wearLengthOffsetZ | : REAL, | Read/Write; |
| geoLengthOffsetY | : REAL, | Read/Write; |
| wearLengthOffsetY | : REAL, | Read/Write; |
| geoOffsetNumber | : INTEGER, | Read/Write; |
| wearOffsetNumber | : INTEGER, | Read/Write; |
| cuttingEdgePosition | : INTEGER, | Read/Write; |
| tipAngle | : REAL, | Read/Write; |
| holderAngle | : REAL, | Read/Write; |
| insertAngle | : REAL, | Read/Write; |
| insertWidth | : REAL, | Read/Write; |
| insertLength | : REAL, | Read/Write; |
| referenceDirectionHolderAngle | : REAL, | Read/Write; |
| directionOfSpindleRotation | : INTEGER, | Read/Write; |
| numberOfTeeth | : INTEGER, | Read/Write; |
| toolLife | : toolLife | |

- 구성 데이터 설명

- edgeNumber 해당 공구에 대한 공구 날의 개수가 하나 이상일 때 각 날을 식별할 수 있는 공구 날 번호를 나타내는 정수형 속성으로 디폴트로 1이 설정됩니다. installTools, registerTools에서는 인덱스 속성이므로 데이터의 읽고 쓰기가 불가능합니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/edgeNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다.
- toolType 해당 공구의 유형을 나타내며, 각 NC 에서 이용 가능한 값들과 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/toolType?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/toolType?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/toolType?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.

| 결과 | FANUC | SIEMENS | CSCAM | MITSUBISHI | KCNC |
| --------------------------------------- | ----- | ------- | ----- | ---------- | ---- |
| 0 : Not defined | | | | | O |
| 10 : General-purpose tool | O | | | | O |
| 11 : Threading tool (Siemens에서는 540) | O | | | | O |
| 12 : Grooving tool | O | | | | O |
| 13 : Round-nose tool | O | | | | O |
| 14 : Point nose straight tool | O | | | | O |
| 15 : Versatile tool | O | | | | |
| 20 : Drill | O | | | O | O |
| 21 : Counter sink tool | O | | | | O |
| 22 : Flat end mill | O | | | O | O |
| 23 : Ball end mill | O | | | O | O |
| 24 : Tap (Siemens에서는 240) | O | | | O | O |
| 25 : Reamer | O | | | | O |
| 26 : Boring tool | O | | | | O |
| 27 : Face mill | O | | | O | O |
| 50 : Radius end mill | | | | O | |
| 51 : 면취 | | | | O | |
| 52 : 선삭 | | | | O | |
| 53 : 홈삽입 | | | | O | |
| 54 : 나사절삭 | | | | O | |
| 55 : 선삭드릴 | | | | O | |
| 56 : 선삭탭 | | | | O | |
| 100 : Milling tool | | O | | | |
| 110 : Ball nose end mill | | O | | | |
| 111 : Conical ball end | | O | | | |
| 120 : End mill | | O | | | |
| 121 : End mill corner rounding | | O | | | |
| 130 : Angle head cutter | | O | | | |
| 131 : Corner rounding angle head cutter | | O | | | |
| 140 : Facing tool | | O | | | |
| 145 : Thread cutter | | O | | | |
| 150 : Side mill | | O | | | |
| 151 : Saw | | O | | | |
| 155 : Bevelled cutter | | O | | | |
| 156 : Bevelled cutter corner | | O | | | |
| 157 : Tap. die-sink. cutter | | O | | | |
| 160 : Drill&thread cut. | | O | | | |
| 200 : Twist drill | | O | | | |
| 205 : Solid drill | | O | | | |
| 210 : Boring bar | | O | | | |
| 220 : Center drill | | O | | | |
| 230 : Countersink | | O | | | |
| 231 : Counterbore | | O | | | |
| 240 : Tap | | O | | | |
| 241 : Fine tap | | O | | | |
| 242 : Tap, Whitworth | | O | | | |
| 250 : Reamer | | O | | | |
| 500 : Roughing tool | | O | | | |
| 510 : Finishing tool | | O | | | |
| 520 : Plunge cutter | | O | | | |
| 530 : Cutting tool | | O | | | |
| 540 : Threading tool | | O | | | |
| 550 : Button tool | | O | | | |
| 560 : Rotary drill | | O | | | |
| 580 : 3D turning probe | | O | | | |
| 585 : Calibrating tool | | O | | | |
| 700 : Slotting saw | | O | | | |
| 710 : 3D probe | | O | | | |
| 711 : Edge finder | | O | | | |
| 712 : Mono probe | | O | | | |
| 713 : L probe | | O | | | |
| 714 : Star probe | | O | | | |
| 725 : Calibrating tool | | O | | | |
| 730 : Stop | | O | | | |
| 731 : Mandrel | | O | | | |
| 732 : Steady rest | | O | | | |
| 900 : Auxiliary tools | | O | | | |

- lengthOffsetNumber FANUC에서 사용되는 lengthOffsetNumber는 해당 공구에 대한 기하학적인 공구 길이와 공구 길이의 마모값에 대한 식별 번호를 나타내는 정수형 속성입니다. SIEMENS에는 해당 속성과 대응되는 데이터로 hNumber가 존재합니다. hNumber 는 SIEMENS에서 ISO 모드로 NC 프로그램을 실행시키는 경우 CNC에 탑재된 공구의 오프셋 값을 가져오기 위해 공구 길이 오프셋 값의 식별자를 나타내는 정수형 속성입니다. hNumber를 사용하기 위해서는 SIEMENS의 MD(Machine Data) 18800이 1로 설정되어야 합니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/lengthOffsetNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/lengthOffsetNumber?machine=i&toolArea=j&tools=k&toolEdge=l&lengthOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/lengthOffsetNumber? machine=i&toolArea=j®isterTools=k&toolEdge=l&lengthOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- geoLengthOffset 해당 공구의 길이 X를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/geoLengthOffset?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/geoLengthOffset?machine=i&toolArea=j&tools=k&toolEdge=l&geoLengthOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/geoLengthOffset?  machine=i&toolArea=j®isterTools=k&toolEdge=l&geoLengthOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- wearLengthOffset 해당 공구의 길이 X에 대한 마모값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/wearLengthOffset?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/wearLengthOffset?machine=i&toolArea=j&tools=k&toolEdge=l&wearLengthOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/wearLengthOffset?machine=i&toolArea=j®isterTools=k&toolEdge=l&wearLengthOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- radiusOffsetNumber FANUC에서 사용되는 radiusOffsetNumber은 해당 공구에 대한 기하학적인 공구 반경과 공구 반경의 마모값의 식별 번호를 나타내는 정수형 속성입니다. SIEMENS에는 해당 속성과 대응되는 데이터로 hNumber가 존재합니다. hNumber는 SIEMENS에서 ISO 모드로 NC 프로그램을 실행시키는 경우 CNC에 탑재된 공구의 오프셋 값을 가져오기 위해 공구 반경 오프셋 값의 식별자를 나타내는 정수형 속성입니다. hNumber를 사용하기 위해서는 SIEMENS의 MD(Machine Data) 18800이 1로 설정되어야 합니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/radiusOffsetNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/radiusOffsetNumber?machine=i&toolArea=j&tools=k&toolEdge=l&radiusOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/radiusOffsetNumber?machine=i&toolArea=j®isterTools=k&toolEdge=l&radiusOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- geoRadiusoffset 해당 공구의 반경을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/geoRadiusOffset?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/geoRadiusOffset?machine=i&toolArea=j&tools=k&toolEdge=l&geoRadiusOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/geoRadiusOffset?machine=i&toolArea=j®isterTools=k&toolEdge=l&geoRadiusOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- wearRadiusOffset 해당 공구의 반경에 대한 마모값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/wearRadiusOffset?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/wearRadiusOffset?machine=i&toolArea=j&tools=k&toolEdge=l&wearRadiusOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/wearRadiusOffset?machine=i&toolArea=j®isterTools=k&toolEdge=l&wearRadiusOffset=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- edgeEnabled 해당 공구의 공구 날에 대한 사용 가능 여부를 나타내는 논리형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/edgeEnabled?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/edgeEnabled?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/edgeEnabled?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- geoLengthOffsetZ 해당 공구의 길이 Z를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/geoLengthOffsetZ ?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/ geoLengthOffsetZ ?machine=i&toolArea=j&tools=k&toolEdge=l& geoLengthOffsetZ =m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/ geoLengthOffsetZ ?machine=i&toolArea=j®isterTools=k&toolEdge=l& geoLengthOffsetZ =m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- wearLengthOffsetZ 해당 공구의 길이 Z에 대한 마모값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/wearLengthOffsetZ?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/wearLengthOffsetZ?machine=i&toolArea=j&tools=k&toolEdge=l&wearLengthOffsetZ=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/wearLengthOffsetZ?machine=i&toolArea=j®isterTools=k&toolEdge=l&wearLengthOffsetZ=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- geoLengthOffsetY 해당 공구의 길이 Y를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/geoLengthOffsetY ?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/ geoLengthOffsetY ?machine=i&toolArea=j&tools=k&toolEdge=l& geoLengthOffsetY =m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/ geoLengthOffsetY ?machine=i&toolArea=j®isterTools=k&toolEdge=l& geoLengthOffsetY =m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- wearLengthOffsetY 해당 공구의 길이 Y에 대한 마모값을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/wearLengthOffsetY?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/wearLengthOffsetY?machine=i&toolArea=j&tools=k&toolEdge=l&wearLengthOffsetY=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/wearLengthOffsetY?machine=i&toolArea=j®isterTools=k&toolEdge=l&wearLengthOffsetY=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- geoOffsetNumber 해당 공구의 길이 X, 길이 Z, 반경의 식별 번호를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/geoOffsetNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/geoOffsetNumber?machine=i&toolArea=j&tools=k&toolEdge=l&geoOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/geoOffsetNumber?machine=i&toolArea=j®isterTools=k&toolEdge=l&geoOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- wearOffsetNumber 해당 공구의 길이 X, 길이 Z, 반경에 대한 마모값들의 식별 번호를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/wearOffsetNumber?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/wearOffsetNumber?machine=i&toolArea=j&tools=k&toolEdge=l&wearOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/wearOffsetNumber?machine=i&toolArea=j®isterTools=k&toolEdge=l&wearOffsetNumber=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- cuttingEdgePosition 해당 공구의 공구 인선 방향을 나타내며, 각 NC 에서 이용 가능한 값들과 대응되는 정수형 속성은 다음과 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/cuttingEdgePosition?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/cuttingEdgePosition?machine=i&toolArea=j&tools=k&toolEdge=l&cuttingEdgePosition=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/cuttingEdgePosition?machine=i&toolArea=j®isterTools=k&toolEdge=l&cuttingEdgePosition=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. [FANUC 공구 인선 번호와 인선 방향]

![image](./lib/NewItem251.png)

| |
| --- |

[SIEMENS 공구 인선 번호와 인선 방향]

![image](./lib/NewItem179.png)

![image](./lib/NewItem178.png)

![image](./lib/NewItem181.png)

![image](./lib/NewItem180.png)

![image](./lib/NewItem183.png)

![image](./lib/NewItem182.png)

![image](./lib/NewItem185.png)

![image](./lib/NewItem184.png)

![image](./lib/NewItem130.png)

![image](./lib/NewItem131.png)

![image](./lib/NewItem132.png)

![image](./lib/NewItem133.png)

![image](./lib/NewItem46.png)

![image](./lib/NewItem47.png)

![image](./lib/NewItem48.png)

![image](./lib/NewItem49.png)

![image](./lib/NewItem50.png)

![image](./lib/NewItem51.png)

![image](./lib/NewItem52.png)

![image](./lib/NewItem53.png)

![image](./lib/NewItem54.png)

![image](./lib/NewItem55.png)

![image](./lib/NewItem56.png)

![image](./lib/NewItem57.png)

![image](./lib/NewItem58.png)

![image](./lib/NewItem59.png)

![image](./lib/NewItem60.png)

![image](./lib/NewItem61.png)

![image](./lib/NewItem62.png)

![image](./lib/NewItem63.png)

![image](./lib/NewItem64.png)

![image](./lib/NewItem65.png)

![image](./lib/NewItem66.png)

![image](./lib/NewItem67.png)

![image](./lib/NewItem68.png)

![image](./lib/NewItem69.png)

![image](./lib/NewItem70.png)

![image](./lib/NewItem71.png)

![image](./lib/NewItem72.png)

![image](./lib/NewItem73.png)

![image](./lib/NewItem74.png)

![image](./lib/NewItem75.png)

![image](./lib/NewItem76.png)

![image](./lib/NewItem77.png)

![image](./lib/NewItem78.png)

![image](./lib/NewItem79.png)

![image](./lib/NewItem80.png)

![image](./lib/NewItem81.png)

![image](./lib/NewItem82.png)

![image](./lib/NewItem83.png)

![image](./lib/NewItem84.png)

![image](./lib/NewItem85.png)

![image](./lib/NewItem86.png)

![image](./lib/NewItem87.png)

![image](./lib/NewItem88.png)

![image](./lib/NewItem89.png)

![image](./lib/NewItem90.png)

![image](./lib/NewItem91.png)

![image](./lib/NewItem92.png)

![image](./lib/NewItem93.png)

![image](./lib/NewItem94.png)

![image](./lib/NewItem95.png)

![image](./lib/NewItem96.png)

![image](./lib/NewItem97.png)

![image](./lib/NewItem98.png)

![image](./lib/NewItem99.png)

![image](./lib/NewItem100.png)

![image](./lib/NewItem101.png)

![image](./lib/NewItem102.png)

![image](./lib/NewItem103.png)

![image](./lib/NewItem104.png)

![image](./lib/NewItem105.png)

![image](./lib/NewItem106.png)

![image](./lib/NewItem107.png)

![image](./lib/NewItem108.png)

![image](./lib/NewItem109.png)

![image](./lib/NewItem110.png)

![image](./lib/NewItem111.png)

![image](./lib/NewItem112.png)

![image](./lib/NewItem113.png)

![image](./lib/NewItem114.png)

![image](./lib/NewItem115.png)

![image](./lib/NewItem116.png)

![image](./lib/NewItem117.png)

![image](./lib/NewItem118.png)

![image](./lib/NewItem119.png)

![image](./lib/NewItem120.png)

![image](./lib/NewItem121.png)

![image](./lib/NewItem122.png)

![image](./lib/NewItem123.png)

![image](./lib/NewItem124.png)

![image](./lib/NewItem125.png)

![image](./lib/NewItem126.png)

![image](./lib/NewItem127.png)

![image](./lib/NewItem128.png)

![image](./lib/NewItem129.png)

![image](./lib/NewItem134.png)

![image](./lib/NewItem135.png)

![image](./lib/NewItem136.png)

![image](./lib/NewItem137.png)

![image](./lib/NewItem138.png)

![image](./lib/NewItem139.png)

![image](./lib/NewItem140.png)

![image](./lib/NewItem141.png)

![image](./lib/NewItem142.png)

![image](./lib/NewItem143.png)

![image](./lib/NewItem144.png)

![image](./lib/NewItem145.png)

![image](./lib/NewItem146.png)

![image](./lib/NewItem147.png)

![image](./lib/NewItem148.png)

![image](./lib/NewItem149.png)

![image](./lib/NewItem150.png)

![image](./lib/NewItem151.png)

![image](./lib/NewItem152.png)

![image](./lib/NewItem153.png)

![image](./lib/NewItem154.png)

![image](./lib/NewItem155.png)

![image](./lib/NewItem156.png)

![image](./lib/NewItem157.png)

![image](./lib/NewItem158.png)

![image](./lib/NewItem159.png)

![image](./lib/NewItem160.png)

![image](./lib/NewItem161.png)

![image](./lib/NewItem163.png)

![image](./lib/NewItem162.png)

![image](./lib/NewItem165.png)

![image](./lib/NewItem164.png)

![image](./lib/NewItem167.png)

![image](./lib/NewItem166.png)

![image](./lib/NewItem169.png)

![image](./lib/NewItem168.png)

![image](./lib/NewItem171.png)

![image](./lib/NewItem170.png)

![image](./lib/NewItem173.png)

![image](./lib/NewItem172.png)

![image](./lib/NewItem175.png)

![image](./lib/NewItem174.png)

![image](./lib/NewItem177.png)

![image](./lib/NewItem176.png)

![image](./lib/NewItem186.png)

![image](./lib/NewItem187.png)

![image](./lib/NewItem188.png)

![image](./lib/NewItem189.png)

![image](./lib/NewItem190.png)

![image](./lib/NewItem191.png)

![image](./lib/NewItem192.png)

![image](./lib/NewItem193.png)

![image](./lib/NewItem194.png)

![image](./lib/NewItem195.png)

![image](./lib/NewItem196.png)

![image](./lib/NewItem197.png)

![image](./lib/NewItem198.png)

![image](./lib/NewItem199.png)

![image](./lib/NewItem200.png)

![image](./lib/NewItem201.png)

![image](./lib/NewItem202.png)

![image](./lib/NewItem203.png)

![image](./lib/NewItem204.png)

![image](./lib/NewItem205.png)

![image](./lib/NewItem206.png)

![image](./lib/NewItem207.png)

![image](./lib/NewItem208.png)

![image](./lib/NewItem209.png)

![image](./lib/NewItem210.png)

![image](./lib/NewItem211.png)

![image](./lib/NewItem212.png)

![image](./lib/NewItem213.png)

![image](./lib/NewItem214.png)

![image](./lib/NewItem215.png)

![image](./lib/NewItem216.png)

![image](./lib/NewItem217.png)

![image](./lib/NewItem218.png)

![image](./lib/NewItem219.png)

![image](./lib/NewItem220.png)

![image](./lib/NewItem221.png)

![image](./lib/NewItem222.png)

![image](./lib/NewItem223.png)

![image](./lib/NewItem224.png)

![image](./lib/NewItem225.png)

![image](./lib/NewItem226.png)

![image](./lib/NewItem227.png)

![image](./lib/NewItem228.png)

![image](./lib/NewItem229.png)

![image](./lib/NewItem230.png)

![image](./lib/NewItem231.png)

![image](./lib/NewItem232.png)

![image](./lib/NewItem233.png)

![image](./lib/NewItem234.png)

![image](./lib/NewItem235.png)

![image](./lib/NewItem236.png)

![image](./lib/NewItem237.png)

![image](./lib/NewItem238.png)

![image](./lib/NewItem239.png)

![image](./lib/NewItem240.png)

![image](./lib/NewItem241.png)

![image](./lib/NewItem242.png)

![image](./lib/NewItem243.png)

![image](./lib/NewItem244.png)

![image](./lib/NewItem245.png)

![image](./lib/NewItem246.png)

![image](./lib/NewItem247.png)

![image](./lib/NewItem248.png)

![image](./lib/NewItem249.png)

![image](./lib/NewItem250.png)

| Tool Type | SIEMENS | | | | | | | |
| ------------------------------ | ------- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | |
| Threading tool (11) | - | - | - | | - | | | |
| Tap (24) | - | - | - | - | | | | |
| Milling tool (100) | - | - | - | - | | | | |
| Ball nose end mill (110) | - | - | - | - | | | | |
| Conical ball end (111) | - | - | - | - | | | | |
| End mill (120) | - | - | - | - | | | | |
| End mill corner rounding (121) | - | - | - | - | | | | |
| Angle head cutter (130) | - | - | - | - | | | | |
| Corn.round.ang.hd.cut (131) | - | - | - | - | | | | |
| Facing tool (140) | - | - | - | - | | | | |
| Thread cutter (145) | - | - | - | - | | | | |
| Side mill (150) | - | - | - | - | | | | |
| Saw (151) | - | - | - | - | | | | |
| Bevelled cutter (155) | - | - | - | - | | | | |
| Bevelled cutter corner (156) | - | - | - | - | | | | |
| Tap. die-sink. cutter (157) | - | - | - | - | | | | |
| Drill&thread cut. (160) | - | - | - | - | | | | |
| Twist drill (200) | - | - | - | - | | | | |
| Solid drill(205) | - | - | - | - | | | | |
| Boring bar (210) | - | - | - | - | | | | |
| Center drill (220) | - | - | - | - | | | | |
| Countersink (230) | - | - | - | - | | | | |
| Counterbore (231) | - | - | - | - | | | | |
| Fine tap (241) | - | - | - | - | | | | |
| Tap, Whitworth (242) | - | - | - | - | | | | |
| Reamer (250) | - | - | - | - | | | | |
| Roughing tool (500) | | | | | | | | |
| Finishing tool (510) | | | | | | | | |
| Plunge cutter (520) | | | | | - | - | - | - |
| Cutting tool (530) | | | | | - | - | - | - |
| Button tool (550) | | | | | | | | |
| Rotary drill (560) | | | | | - | - | - | - |
| 3D turning probe (580) | - | - | - | - | | | | |
| Calibrating tool (585) | | | | | | | | |
| Slotting saw (700) | - | - | - | - | | | | |
| 3D probe (710) | - | - | - | - | | | | |
| Edge finder (711) | - | - | - | - | | | | |
| Mono probe (712) | - | - | - | - | | | | |
| L probe (713) | - | - | - | - | | | | |
| Star probe (714) | - | - | - | - | | | | |
| Calibrating tool (725) | - | - | - | - | | | | |
| Stop (730) | - | - | - | - | | | | |
| Mandrel (731) | - | - | - | - | | - | | - |
| Steady rest (732) | - | - | | | - | - | - | |
| Auxility tools (900) | - | - | - | - | | | | |

- tipAngle 해당 공구의 팁 각을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/tipAngle?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/tipAngle?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/tipAngle?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- holderAngle 선반 공구에만 해당하는 형상 정보로, 해당 공구의 holder angle을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/holderAngle?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/holderAngle?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/holderAngle?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- insertAngle 선반 공구에만 해당하는 형상 정보로, 해당 공구의 insert angle을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/insertAngle?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/insertAngle?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/insertAngle?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- insertWidth (SIEMENS only) 해당 공구에 대한 인선의 너비를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/insertWidth?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/insertWidth?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/insertWidth?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- insertLength (SIEMENS only) 선반 공구에만 해당하는 형상 정보로, 해당 공구에 대한 인선의 길이를 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/insertLength?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/insertLength?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/insertLength?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- referenceDirectionHolderAngle (SIEMENS only) 선반 공구에만 해당하는 형상 정보로, 해당 공구에 대한 holder angle의 참조 방향을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/referenceDirectionHolderAngle?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/referenceDirectionHolderAngle?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/referenceDirectionHolderAngle?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- directionOfSpindleRotation (SIEMENS only) 해당 공구의 스핀들 회전 방향을 나타내며, 각 방향에 대응되는 정수형 속성은 다음 표와 같습니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/directionOfSpindleRotation?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/directionOfSpindleRotation?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/directionOfSpindleRotation?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.

| SIEMENS |
| ---------- |
| 0 : 회전 없음 |
| 1 : 시계 방향 |
| 2 : 반시계 반향 |

- numberOfTeeth (SIEMENS only) 해당 공구에 대한 공구 날의 개수를 나타내는 정수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/numberOfTeeth?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/numberOfTeeth?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/numberOfTeeth?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다.
- toolLife toolEdge의 toolLife 데이터는 해당 공구에 대한 수명 정보를 나타내며, toolLife 타입으로 정의됩니다. 자세한 설명은 ' 5.2.1.4.2:A.1 toolLife' 절에서 확인할 수 있습니다.

---

## A.1 toolLife
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 5.2.1.4 toolArea 5.2.1.4.2 activeTool/tools A. toolEdge 

- 개요 toolEdge의 toolLife 데이터는 해당 공구에 대한 수명 정보를 나타냅니다. 수명 측정 단위, 최대 수명, 잔여 수명, 현재 수명, 알람 수명 등을 포함합니다.

- 데이터 구성

| activateTool의 toolLife | | |
| ---------------------- | ------- | ---------- |
| maxToolLife | : REAL, | Read-only; |
| restToolLife | : REAL, | Read-only; |
| toolLifeCount | : REAL, | Read-only; |
| toolLifeAlarm | : REAL, | Read-only; |

| installTools와 registerTools의 toolLife | | |
| ------------------------------------- | ------- | ----------- |
| maxToolLife | : REAL, | Read/Write; |
| restToolLife | : REAL, | Read/Write; |
| toolLifeCount | : REAL, | Read/Write; |
| toolLifeAlarm | : REAL, | Read/Write; |

- 구성 데이터 설명

- maxToolLife 해당 공구의 최대 수명을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/toolLife/maxToolLife?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/toolLife/maxToolLife?machine=i&toolArea=j&tools=k&toolEdge=l&maxToolLife=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/toolLife/maxToolLife?machine=i&toolArea=j®isterTools=k&toolEdge=l&maxToolLife=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- restToolLife 해당 공구의 잔여 수명을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/toolLife/restToolLife?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/toolLife/restToolLife?machine=i&toolArea=j&tools=k&toolEdge=l&restToolLife=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/toolLife/restToolLife?machine=i&toolArea=j®isterTools=k&toolEdge=l&restToolLife=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- toolLifeCount 해당 공구의 공구 수명을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/toolLife/toolLifeCount?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/toolLife/toolLifeCount?machine=i&toolArea=j&tools=k&toolEdge=l&toolLifeCount=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다. registerTools data://machine/toolArea/registerTools/toolEdge/toolLife/toolLifeCount?machine=i&toolArea=j®isterTools=k&toolEdge=l&toolLifeCount=m i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. m 은 몇 번째 공구 그룹인지를 의미하는 정수값입니다. FANUC의 tool life management 옵션이 탑재된 장비에서 사용하며, 이외의 경우 1로 표기합니다.
- toolLifeAlarm (SIEMENS only) 공구 사용에 대한 알람을 줄 수 있도록, 해당 공구의 한계 수명을 나타내는 실수형 속성입니다.

주소 표기는 다음과 같이 합니다. activeTool data://machine/channel/activeTool/toolEdge/toolLife/toolLifeAlarm?machine=i&channel=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 채널인지를 의미하는 정수값입니다. installTools data://machine/toolArea/tools/toolEdge/toolLife/toolLifeAlarm?machine=i&toolArea=j&tools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. registerTools data://machine/toolArea/registerTools/toolEdge/toolLife/toolLifeAlarm?machine=i&toolArea=j®isterTools=k&toolEdge=l i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 공구 영역인지를 의미하는 정수값입니다. k 는 몇 번째 공구 인덱스 번호인지를 의미하는 정수값입니다. l 는 몇 번째 공구 모서리인지를 의미하는 정수값입니다. 

---

##### 5.2.1.5 buffer
5. CNC 공통 데이터 모델 5.2 데이터 모델의 각 데이터 설명 5.2.1 machine 

- 개요 buffer 데이터는 CNC 구동계에 내장된 센서 데이터 수집에 대한 정보를 나타냅니다. buffer의 stream별로 센서 데이터를 수집합니다. Kcnc와 Fanuc만 지원합니다. 수집의 시작은 "수집 시작 함수"(Api.startTimeSeries)를 통해 이루어집니다. 수집의 종료는 "수집 종료 함수"(Api.endTimeSeries) 혹은 수집 완료(1회 수집 모드시)로 이루어집니다. 센서 데이터는 콜백 함수를 통해 받을 수 있습니다. 수집 시작 전에 콜백함수를 등록해야 합니다. ※ 콜백함수의 등록과 수집 시작 함수와 수집 종료 함수는 "6.TORUS User API"를 참조하십시오.

- 데이터 구성

| buffer | | |
| ---------------------- | ------------------------- | ----------- |
| bufferEnabled | : BOOLEAN, | Read-only; |
| numberOfStream | : INTEGER, | Read-only; |
| statusOfStream | : INTEGER, | Read/Write; |
| modOfStream | : INTEGER, | Read/Write; |
| machineChannelOfStream | : INTEGER, | Read/Write; |
| periodOfStream | : INTEGER, | Read/Write; |
| triggerOfStream | : INTEGER, | Read/Write; |
| frequencyOfStream | : INTEGER, | Read/Write; |
| stream | : LIST [1:N] OF “stream”; | |
| streamEnabled | : BOOLEAN, | Read/Write; |
| streamFrequency | : INTEGER, | Read/Write; |
| streamCategory | : INTEGER, | Read/Write; |
| streamSubcategory | : INTEGER, | Read/Write; |
| streamType | : INTEGER, | Read/Write; |
| streamStartBit | : INTEGER, | Read/Write; |
| streamEndBit | : INTEGER, | Read/Write; |
| value | : REAL, | Read-only; |

- 구성 데이터 설명

- bufferEnabled 해당 버퍼의 사용 가능 여부를 나타내는 논리형 속성입니다. 오직 1번 버퍼만 사용 가능합니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/bufferEnabled?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.
- numberOfStream 해당 버퍼의 최대 스트림 개수를 나타내는 정수형 속성입니다. 스트림은 통상 센서의 채널과 같은 의미입니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/numberOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.
- statusOfStream 해당 버퍼의 스트림 상태를 나타내는 정수형 속성입니다. 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/statusOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.

| 결과 | 수정 가능 여부 | 설명 |
| ----------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 : 설정 가능 | O | 설정 가능 상태에서만 buffer와 stream의 속성 값을 변경할 수 있습니다. |
| 1 : 수집 가능 | O | 수집 가능 상태에서는 buffer와 stream의 속성 값을 변경할 수 없습니다. "수집 시작 함수"로 수집 시작을 명령 할 수 있습니다. ※ 수집시작함수는 UserAPI - Api.startTimeSeries(버퍼, MachineID) 입니다. |
| 2 : 수집 대기 | X | 수집이 시작되어 수집 대기 상태입니다. Trigger를 사용하여 대기 중일 때를 표시합니다. |
| 3 : 수집 중 | X | 수집 중 상태입니다. |
| 4 : 수집 대기 혹은 수집 중 | X | 2와 3이 구분되지 않는 경우에 사용됩니다. |
| 5 : 수집 완료/종료 | X | 1회 수집 모드일때 1회 수집후 수집이 완료되었거나 반복 수집 모드일때 "수집 종료 함수"로 수집이 종료된 경우, 즉 정상적으로 수집이 완료/종료된 경우입니다. "수집 시작 함수"로 다시 수집 시작을 명령 할 수 있습니다. ※ 수집종료함수는 UserAPI - Api.endTimeSeries(버퍼, MachineID) 입니다. |
| -1 : CNC 연결 실패 | X | 수집 시작을 시도했으나 CNC에 연결 실패한 경우입니다. buffer는 수집 시작시에 별도의 연결을 생성합니다. |
| -2 : 설정값 적용 실패 | X | 수집 시작을 시도했으나 설정값 적용이 실패한 경우입니다. 설정값이 해당 CNC에서 유효하지 않은 경우입니다. |

- modOfStream 해당 버퍼의 스트림 수집 모드를 나타내는 정수형 속성입니다. 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/modOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.

| 결과 | 설명 |
| --------- | --------------------------------------------------------------------------- |
| 0 : 반복 수집 | 수집을 시작하면 수집 종료를 하기 전까지 계속 반복하여 수집합니다. 수집 중에는 statusOfStream 값은 3 또는 4가 됩니다. |
| 1 : 1회 수집 | 수집을 시작하면 1회 수집이 완료되면 수집이 자동으로 종료됩니다. 수집 종료 후에 statusOfStream 값은 5가 됩니다. |

- machineChannelOfStream 해당 버퍼의 스트림 수집 시 사용할 계통을 나타내는 정수형 속성입니다. Kcnc는 단일 계통을 사용하므로 1로 고정됩니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/machineChannelOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.
- periodOfStream 해당 버퍼의 스트림 수집 시 1회 수집 기간을 나타내는 정수형 속성입니다. (최대값 : 10000 → 10초) (단위 : ms) 한번의 수집이 종료되면 콜백함수가 발동됩니다. 반복 수집일 경우 콜백함수가 종료되고 바로 다음 수집이 시작됩니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/periodOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.
- triggerOfStream 해당 버퍼의 스트림 수집 시 사용할 트리거를 나타내는 정수형 속성입니다. 값이 0이면 수집 시작 명령시 대기 없이 수집을 바로 시작합니다. 1 이상의 값일 경우에는 수집 대기 상태에 들어가고 트리거 값과 동일한 sequenceNumber에 도달하면 수집을 시작합니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/triggerOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.
- frequencyOfStream 해당 버퍼의 스트림 수집 시 공통 사용할 주파수를 나타내는 정수형 속성입니다. (기본값 : 1000) (단위 : Hz) 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다. Write할 경우, 모든 스트림의 주파수를 한번에 설정합니다. Read할 경우 모든 스트림의 주파수가 동일하지 않으면 오류를 반환합니다. 주파수는 스트림별로도 설정이 가능합니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/frequencyOfStream?machine=i&buffer=j i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다.

| 결과 (단위 : Hz) | Kcnc | Fanuc |
| ------------ | ---- | ------------------------------------ |
| 1000 | O | O |
| 4000 | | O (일부 Category-Subcategory에서만 사용 가능) |

- streamEnabled 해당 스트림의 사용 가능 여부를 나타내는 논리형 속성입니다. 1번 스트림은 기본적으로 true 상태입니다. 나머지 버퍼는 true로 설정해야 사용 가능합니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamEnabled?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.
- streamFrequency 해당 스트림의 수집 시 사용할 주파수를 나타내는 정수형 속성입니다. (기본값 : 1000) (단위 : Hz) 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamFrequency?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.

| 결과 (단위 : Hz) | Kcnc | Fanuc |
| ------------ | ---- | ------------------------------------ |
| 1000 | O | O |
| 4000 | | O (일부 Category-Subcategory에서만 사용 가능) |

- streamCategory 해당 스트림의 수집 대상 카테고리를 나타내는 정수형 속성입니다. 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamCategory?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.

| 결과 | Kcnc | Fanuc 서브카테고리에 따라 카테코리 타입이 달라집니다. |
| --- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 | X | Subcategory-Axis: Summation of position feedback pulse data (POSF) Subcategory-Spindle: Summation of position feedback pulse data (CSPOS) |
| 1 | 상태정보 X | Subcategory-Axis: Position error (ERR) Subcategory-Spindle: Moter speed (SPEED) |
| 2 | 상태정보 Y | Subcategory-Axis: Velocity command (VCMD) Subcategory-Spindle: Torque command (TCMD) |
| 3 | 상태정보 G | Subcategory-Axis: Torque command (TCMD) Subcategory-Spindle: Moter speed command (VCMD) |
| 4 | 상태정보 F | Subcategory-Axis: Speed feedback signal (SPEED) Subcategory-Spindle: Position error (ERR) |
| 5 | 상태정보 R | Subcategory-Axis: Estimated disturbance torque (DTRQ) Subcategory-Spindle: Load meter data (LMDAT) |
| 6 | 상태정보 T | Subcategory-Axis: Synchronous error on rigid tapping (SYNC) Subcategory-Spindle: Spindle load torque (DTRQ) |
| 7 | 상태정보 C | Subcategory-Axis: OVC simulation data (OVCLV) Subcategory-Spindle: Amplitude of moter current (INORM) |
| 8 | 상태정보 D | Subcategory-Axis: Effective current (IEFF) Subcategory-Spindle: Moter winding temperature (MTTMP) |
| 9 | 상태정보 SN | Subcategory-Axis: DC link voltage(VDC) Subcategory-Spindle: Spindle axis power consumption(EPMTR) |
| 10 | 상태정보 SV | Subcategory-Axis: Semi-Full error(SFERR) Subcategory-Spindle: Frequency of disturbance torque(FREQ) |
| 11 | 상태정보 SSV | Subcategory-Axis: Analog signal command(ALGCMD) Subcategory-Spindle: Gain data(GAIN) |
| 12 | 상태정보 MS | Subcategory-Axis: Analog signal feedback(ALGFB) Subcategory-Spindle: Torque command 2(TCMD2) |
| 13 | X | Subcategory-Axis: R-phase current(IR) Subcategory-Spindle: A/D data of motor sensor (A phase)(PA1) |
| 14 | X | Subcategory-Axis: R-phase current(PDM slave1)(IR1) Subcategory-Spindle: A/D data of motor sensor (B phase)(PB1) |
| 15 | X | Subcategory-Axis: R-phase current(PDM slave2)(IR2) Subcategory-Spindle: A/D data of spindle sensor (A phase)(PA2) |
| 16 | X | Subcategory-Axis: R-phase current(PDM slave3)(IR3) Subcategory-Spindle: A/D data of spindle sensor (B phase)(PB2) |
| 17 | X | Subcategory-Axis: R-phase current(PDM slave4)(IR4) Subcategory-Spindle: Velocity error(VERR) |
| 18 | X | Subcategory-Axis: S-phase current(IS) Subcategory-Spindle: Spindle speed(SPSPD) |
| 19 | X | Subcategory-Axis: S-phase current(PDM slave1)(IS1) Subcategory-Spindle: Present value of loadmeter (Normalized by cont. rated output(LMDTC) |
| 20 | X | Subcategory-Axis: S-phase current(PDM slave2)(IS2) Subcategory-Spindle: Maximum value of loadmeter at the present speed (Normalized by cont. rated output)(LMMAX) |
| 21 | X | Subcategory-Axis: S-phase current(PDM slave3)(IS3) Subcategory-Spindle: Duration time for cutting(DURTM) |
| 22 | X | Subcategory-Axis: S-phase current(PDM slave4)(IS4) Subcategory-Spindle: X |
| 23 | X | Subcategory-Axis: Reactive current(ID) Subcategory-Spindle: X |
| 24 | X | Subcategory-Axis: Active current(IQ) Subcategory-Spindle: X |
| 25 | X | Subcategory-Axis: Motor winding temperature(MTTMP) Subcategory-Spindle: X |
| 26 | X | Subcategory-Axis: Pulsecoder temperature(PCTMP) Subcategory-Spindle: X |
| 27 | X | Subcategory-Axis: Velocity command without FF(VCOUT) Subcategory-Spindle: X |
| 28 | X | Subcategory-Axis: Advanced velocity command(VCC0) Subcategory-Spindle: X |
| 29 | X | Subcategory-Axis: Backlash acceleration amount(BLACL) Subcategory-Spindle: X |
| 30 | X | Subcategory-Axis: Absolute position detected internal pulse coder(ABS) Subcategory-Spindle: X |
| 31 | X | Subcategory-Axis: Vibration frequency(FREQ) Subcategory-Spindle: X |
| 32 | X | Subcategory-Axis: Vibration torque command(FRTCM) Subcategory-Spindle: X |
| 33 | X | Subcategory-Axis: DC link voltage(VDC) Subcategory-Spindle: X |
| 34 | X | Subcategory-Axis: Acceleration feedback in direction specified by No.2277#7,6,5(ACC) Subcategory-Spindle: X |
| 35 | X | Subcategory-Axis: 1st direction acceleration feedback(ACC1) Subcategory-Spindle: X |
| 36 | X | Subcategory-Axis: 2nd direction acceleration feedback(ACC2) Subcategory-Spindle: X |
| 37 | X | Subcategory-Axis: 3rd direction acceleration feedback(ACC3) Subcategory-Spindle: X |
| 38 | X | Subcategory-Axis: Vibration velocity command(FRVCM) Subcategory-Spindle: X |
| 39 | X | Subcategory-Axis: Backlash compensation(BLCMP) Subcategory-Spindle: X |
| 40 | X | Subcategory-Axis: Backlash acceleration amount 1(BLAC1) Subcategory-Spindle: X |
| 41 | X | Subcategory-Axis: Backlash acceleration amount 2(BLAC2) Subcategory-Spindle: X |
| 42 | X | Subcategory-Axis: Smart backlash compensation (position compensation amount)(SMTBKL) Subcategory-Spindle: X |
| 43 | X | Subcategory-Axis: Estimated load torque for Smart backlash compensation(SMTTRQ) Subcategory-Spindle: X |
| 44 | X | Subcategory-Axis: Compensation amount of smart backlash (for full-closed)(SMTBAC) Subcategory-Spindle: X |
| 45 | X | Subcategory-Axis: Analog signal offset(ALGOFS) Subcategory-Spindle: X |
| 46 | X | Subcategory-Axis: Analog signal offset 2(ALGOF2) Subcategory-Spindle: X |

- streamSubcategory 해당 스트림의 수집 대상 서브카테고리를 나타내는 정수형 속성입니다. 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamSubcategory?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.

| Kcnc | Fanuc |
| ----------------------------------------------------------------------- | -------------------------------------------- |
| 각 상태정보의 하위 항목번호 | 1 이상의 정수 : Axis 번호 예) 1 → X축, 2 → Y축, 3 → Z축 |
| -1 이하의 정수 : Spindle 번호 예) -1 → 1번Spindle, -2 → 2번Spindle, 3 → 3번Spindle | |

- streamType 해당 스트림의 수집 유형을 나타내는 정수형 속성입니다. 이용 가능한 값들과 대응되는 정수형 속성은 아래 표와 같습니다. Kcnc 전용의 속성입니다. (기본값 : 1)

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamType?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.

| 결과 | 설명 |
| --- | -------- |
| 0 | Bit |
| 1 | Resistor |

- streamStartBit 해당 스트림의 수집 유형이 Bit일때 StartBit를 나타내는 정수형 속성입니다. 수집 유형이 Bit가 아닐때는 사용되지 않습니다. Kcnc 전용의 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamStartBit?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.
- streamEndBit 해당 스트림의 수집 유형이 Bit일때 EndBit를 나타내는 정수형 속성입니다. 수집 유형이 Bit가 아닐때는 사용되지 않습니다. Kcnc 전용의 속성입니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/streamEndBit?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다.
- value 해당 스트림의 마지막 수집 데이터를 나타내는 실수형 속성입니다. 콜백함수와는 별개로 마지막 데이터를 보여줍니다.

주소 표기는 다음과 같이 합니다. data://machine/buffer/stream/value?machine=i&buffer=j&stream=k i 는 몇 번째 장비인지를 의미하는 정수값입니다. j 는 몇 번째 버퍼인지를 의미하는 정수값입니다. k 는 몇 번째 스트림인지를 의미하는 정수값입니다. 

---

## 6. 비가공장비 데이터 모델 

TORUS Platform 에서는 비가공장비 데이터 모델을 "Device Data Model" 이라고 합니다. 

---

### 6.1 비가공장비 데이터 모델의 정의 
6. 비가공장비 데이터 모델 

TORUS Platform에서는 공작기계를 제외한 다른 생산.제조 장치를 비가공장비라 칭합니다. TORUS Platform의 비가공장비 데이터 모델은 공작기계를 제외한 다른 생산.제조 장치와 연결하여 장치의 상태를 모니터링하거나 제어 명령을 지령하는 데 사용하는 메모리 구조 입니다. TORUS Platform은 비가공장비와 연결을 위해 산업용 통신 프로토콜을 지원하며, 

---

#### 6.1.1 비가공장비 데이터 모델의 구조 
6. 비가공장비 데이터 모델 6.1 비가공장비 데이터 모델의 정의 

- TORUS Platform  비가공장비 데이터 모델
TORUS Platform에서 지원하는 비가공장비 데이터 모델(Device Data mode)은 Client와 Server 두 종류를 지원하며 구조는 다음 그림과 같습니다. TORUS Platform이 지원하는 산업용 통신 서버의 데이터를 읽고 쓰는 경우에는 아래 그림의 우측에 표시된 데이터 모델이 적용됩니다. 즉, TORUS Platform이 구동하는 서버 당 메모리는 하나만 할당 됩니다.

![image](./lib/NewItem%205.png)
비가공 장비와 TORUS Platform 간 연결일 경우에는 위 그림의 좌측에 표시된 데이터 모델이 적용됩니다. 즉, 하나의 비가공장비 통신에 다수의 메모리 구조를 할당 할 수 있습니다. 이를 address mapping 관계로 표시하면 아래의 그림과 같습니다.

![image](./lib/NewItem485.png)
■ Client 통신용 비가공장비 데이터 모델 TORUS Platform에서 지원하는 Client용 비가공장비 통신 기능은 연결하는 각 Device 마다 다수의 memory를 구성할 수 있으며, 각 memory는 10개의 memory block으로 구성됩니다. Device Data memory 구조를 간략히 표로 나타내면 다음과 같습니다.

| device [ ] | memory [ ] | rbitBlock [ ] |
| --------------- | ---------- | ------------- |
| bitBlock [ ] | | |
| rbyteBlock [ ] | | |
| byteBlock [ ] | | |
| rwordBlock [ ] | | |
| wordBlock [ ] | | |
| rdwordBlock [ ] | | |
| dwordBlock [ ] | | |
| rqwordBlock [ ] | | |
| qwordBlock [ ] | | |

■ 서버 통신용 비가공장비 데이터 모델 TORUS Platform이 지원하는 서버 통신용 비가공장비 데이터 모델은 각 구동 가능한 서버 마다 단일 memory로 구성되며, 해당 memory는 10개의 memory block으로 구성됩니다. memory block의 속성은 다음과 같습니다.

| deviceserver [ ] | memory | rbitBlock [ ] |
| ---------------- | ------ | ------------- |
| bitBlock [ ] | | |
| rbyteBlock [ ] | | |
| byteBlock [ ] | | |
| rwordBlock [ ] | | |
| wordBlock [ ] | | |
| rdwordBlock [ ] | | |
| dwordBlock [ ] | | |
| rqwordBlock [ ] | | |
| qwordBlock [ ] | | |

■ 각 memory block의 속성 TORUS Platform이 지원하는 비가공장비(서버/클라이언트) 데이터 모델을 구성하는 각 memory block의 속성은 다음 표와 같습니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | -------------------------------------- | -------------------- | --------------------- |
| 1 | rbitBlock | 1bit | 1~65536 | boolean | ~ 65536 bit (8kB) | input type, read-only |
| 2 | bitBlock | 1bit | 1~65536 | boolean | ~ 65536 bit (8kB) | |
| 3 | rbyteBlock | 8bit | 1~65536 | char, unsigned char | ~ 65536 byte (64kB) | input type, read-only |
| 4 | byteBlock | 8bit | 1~65536 | char, unsigned char | ~ 65536 byte (64kB) | |
| 5 | rwordBlock | 16bit | 1~65536 | short, unsigned short | ~131072 byte (128kB) | input type, read-only |
| 6 | wordBlock | 16bit | 1~65536 | short, unsigned short | ~131072 byte (128kB) | |
| 7 | rdwordBlock | 32bit | 1~65536 | float, integer, unsigned integer, long | ~262144 byte (256kB) | input type, read-only |
| 8 | dwordBlock | 32bit | 1~65536 | float, integer, unsigned integer, long | ~262144 byte (256kB) | |
| 9 | rqwordBlock | 64bit | 1~65536 | double, longlong | ~524288 byte (512kB) | input type, read-only |
| 10 | qwordBlock | 64bit | 1~65536 | double, longlong | ~524288 byte (512kB) | |

---

### 6.2 비가공장비 데이터 설명
6. 비가공장비 데이터 모델 

TORUS Platform이 지원하는 비가공장비 통신 및 산업용 통신 서버를 위한 데이터에 대한 설명 입니다. 

---

#### 6.2.1 rbitBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기 전용 bit type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | --------------- | ----------------- | --------------------- |
| 1 | rbitBlock | 1bit | 1~65536 | boolean | ~ 65536 bit (8kB) | input type, read-only |

- 데이터 어드레스 및 필터 설명

- 비가공장비 통신을 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/rbitBlock?device=i&memory=j&rbitBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/rbitBlock?deviceserver=i&rbitBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.2 bitBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기/쓰기가 가능한 bit type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | --------------- | ----------------- | --- |
| 2 | bitBlock | 1bit | 1~65536 | boolean | ~ 65536 bit (8kB) | |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/bitBlock?device=i&memory=j&bitBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/bitBlock?deviceserver=i&bitBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 bitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.3 rytetBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기 전용 byte type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | ------------------- | ------------------- | --------------------- |
| 3 | rbyteBlock | 8bit | 1~65536 | char, unsigned char | ~ 65536 byte (64kB) | input type, read-only |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/rbyteBlock?device=i&memory=j&rbyteBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/rbyteBlock?deviceserver=i&rbyteBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 rbyteBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.4 byteBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기/쓰기가 가능한 byte type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | ------------------- | ------------------- | --- |
| 4 | byteBlock | 8bit | 1~65536 | char, unsigned char | ~ 65536 byte (64kB) | |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/byteBlock?device=i&memory=j&byteBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/byteBlock?deviceserver=i&byteBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 byteBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.5 rwordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기 전용 word type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | --------------------- | -------------------- | --------------------- |
| 5 | rwordBlock | 16bit | 1~65536 | short, unsigned short | ~131072 byte (128kB) | input type, read-only |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/rwordBlock?device=i&memory=j&rwordBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/rwordBlock?deviceserver=i&rwordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 rwordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.6 wordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기/쓰기가 가능한 word type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | --------------------- | -------------------- | --- |
| 6 | wordBlock | 16bit | 1~65536 | short, unsigned short | ~131072 byte (128kB) | |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/wordBlock?device=i&memory=j&wordtBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/wordBlock?deviceserver=i&wordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 wordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.7 rdwordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기 전용 dword type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | -------------------------------- | -------------------- | --------------------- |
| 7 | rdwordBlock | 32bit | 1~65536 | float, integer, unsigned integer | ~262144 byte (256kB) | input type, read-only |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/rdwordBlock?device=i&memory=j&rdwordBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/rdwordBlock?deviceserver=i&rdwordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 rdwordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.8 dwordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기/쓰기가 가능한 dword type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | -------------------------------- | -------------------- | --- |
| 8 | dwordBlock | 32bit | 1~65536 | float, integer, unsigned integer | ~262144 byte (256kB) | |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/dwordBlock?device=i&memory=j&dwordBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/dwordBlock?deviceserver=i&dwordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 dwordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.9 rqwordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기 전용 qword type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | ---------------------- | -------------------- | --------------------- |
| 9 | rqwordBlock | 64bit | 1~65536 | double, long, longlong | ~524288 byte (512kB) | input type, read-only |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/rqwordBlock?device=i&memory=j&rqwordBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/rqwordBlock?deviceserver=i&rqwordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 rqwordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

#### 6.2.10 qwordBlock
6. 비가공장비 데이터 모델 6.2 비가공장비 데이터 설명 

- 개요 읽기/쓰기가 가능한 qword type 데이터 블록입니다.

| Memory Block type number | Memory Block name | 1 어드레스 당 크기 | 어드레싱 가능 개수 | 할당가능한 Data type | 메모리 크기 | 비고 |
| ------------------------ | ----------------- | ----------- | ---------- | ---------------------- | -------------------- | --- |
| 10 | qwordBlock | 64bit | 1~65536 | double, long, longlong | ~524288 byte (512kB) | |

- 데이터 어드레스 및 필터 설명

- 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://device/memory/qwordBlock?device=i&memory=j&qwordBlock=k i 는 몇 번째 비 가공장비인지를 의미하는 정수 값입니다. deviceList.xml에 정의된 ID를 사용합니다. 만약, deviceList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 해당 장비와 매칭되는 몇 번째 메모리 인지를 나타냅니다. 각 App에서 지정한 mapping table에 정의된 memory ID를 사용합니다. 만약, mapping table에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. k 는 rbitBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다.
- TORUS Platform이 구동하는 산업용 통신 서버의 데이터 액세스를 위한 데이터 어드레스 및 필터 구성 통신 요청 시, 다음과 같이 데이터 어드레스와 필터를 구성합니다.

data://deviceserver/memory/qwordBlock?deviceserver=i&qwordBlock=j i 는 몇 번째 서버인지를 의미하는 정수 값입니다. DeviceCommSvrList.xml에 정의된 ID를 사용합니다. 만약, DeviceCommSvrList.xml에 정의되지 않은 ID를 사용할 경우, 오류가 발생합니다. j 는 qwordBlock의 몇 번째 데이터를 이용할 것인지 지정합니다. 각 App에서 지정한 mepping table에 정의된 address를 사용합니다. 만약, mapping table에 정의되지 않은 어드레스를 사용할 경우 오류가 발생합니다. 

---

## 7. TORUS Platform User API

---

### 7.1 API 정의
7. TORUS Platform User API 

TORUS Platform 기반의 S/W Application 개발을 지원하기 위해 TORUS Platform User API를 지원합니다. 

---

#### 7.1.1 API List
7. TORUS Platform User API 7.1 API 정의 

TORUS Platform에서 지원하는 User API는 다음과 같습니다.

| 구분 | API ( C# ) | API ( C++ ) | 설명 |
| ----------------------------- | ----------------------- | ----------------------------------------------------------------------- | ----------------------------------------------- |
| API Initialize | Initialize | Initialize | API 라이브러리를 초기화하는 기능을 제공하는 API 함수입니다. |
| Data Access | getData | getData | 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다. |
| getData ( 주기 다양화 적용 ) | getData ( 주기 다양화 적용 ) | 데이터 요청 주기에 따라 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다. | |
| getDataEx | getDataEx | App의 Hide 상태에 따라 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다. | |
| getGModal | getGModal | 설정된 Modal 가져오는 API 함수 입니다. | |
| getExModal | getExModal | 설정된 Modal 가져오는 API 함수 입니다. | |
| updateData | updateData | 지정한 데이터의 값을 업데이트 하는 기능을 제공하는 API 함수 입니다. | |
| insertData | insertData | 새로운 데이터를 추가하는 기능을 제공하는 API 함수 입니다. | |
| deleteData | deleteData | 기존 데이터를 삭제하는 기능을 제공하는 API 함수 입니다. | |
| subscribeData | subscribeData | 특정 데이터를 Manager에 등록하는 API 함수입니다. | |
| subscribeDataResult | subscribeDataResult | 특정 데이터의 변경을 통보 받도록 요청하는 API 함수입니다. | |
| unsubscribeData | unsubscribeData | 특정 데이터의 변경 통보 받는 것을 해제하는 API 함수입니다. | |
| subscribeDataClear | subscribeDataClear | App에서 subscribeData로 등록한 Address를 모두 제거하는 API 함수입니다. | |
| getDataAsync | getDataAsync | 비동기로 Data를 읽어오는 기능을 제공하는 API 함수입니다. | |
| getDataAsyncResult | getDataAsyncResult | 他App에서 getDataAsync를 요청했을때 결과값을 보내는 API함수입니다. | |
| getToolOffsetData | getToolOffsetData | 설정된 Tool offset data를 가져오는 API 함수 입니다. | |
| setToolOffsetData | setToolOffsetData | Tool offset data를 NC에 설정하는 API 함수 입니다. | |
| getGudData | getGudData | 설정된 Gud data를 가져오는 API 함수 입니다. | |
| setGudData | setGudData | Gud data를 NC에 설정하는 API 함수 입니다. | |
| Application Control | constrolApp | constrolApp | Application에 특정 명령을 전달하는 기능을 제공하는 API 함수입니다. |
| broadcast | broadcast | 모든 Application에 명령을 전달하는 기능을 제공하는 API 함수입니다. | |
| DeliveryFile | DeliveryFile | Application에서 지정된 Application에 File Stream 객체를 전달하는 기능을 제공하는 API 함수입니다. | |
| Terminate | Terminate | API 라이브러리를 종료하는 기능을 제공하는 API 함수입니다. | |
| GuidLoaded | GuidLoaded | 해당 Application Load 되었음을 Platform에 알리는 기능을 제공하는 API 함수 입니다. | |
| GuidClosed | GuidClosed | 해당 Application이 정상종료 되었음을 Platform에 알려주는 기능을 제공하는 API 함수 입니다. | |
| PLC DataAccess API | getPlcSignal | getPlcSignal | PLC Data를 읽어오는 기능을 제공하는 API 함수입니다. |
| setPlcSignal | setPlcSignal | PLC Data를 갱신하는 기능을 제공하는 API 함수입니다. | |
| Extra API | getMachinesInfo | getMachinesInfo | 플랫폼에 연결된 다중 장비의 속성을 확인 할수 있도록 정보를 제공해주는 함수 입니다. |
| File Access API | getAttributeExists | getAttributeExists | NC의 파일 혹은 폴더가 존재하는지 확인하는 기능을 제공하는 API 함수입니다. |
| getAttributeType | getAttributeType | 입력경로가 파일인지 폴더인지를 확인하는 기능을 제공하는 API 함수입니다. | |
| getAttributeIsNc | getAttributeIsNc | 파일 혹은 폴더의 NC 내 위치 여부를 확인하는 기능을 제공하는 API 함수입니다. | |
| getAttributeLogicalPath | getAttributeLogicalPath | 객채의 논리적 경로를 가져오는 기능을 제공하는 API 함수입니다. | |
| getAttributeName | getAttributeName | 파일 혹은 폴더의 이름 정보를 가져오는 기능을 제공하는 API 함수입니다. | |
| getAttributePath | getAttributePath | 파일 객체의 실제 경로를 가져오는 기능을 제공하는 API 함수입니다. | |
| getAttributeSize | getAttributeSize | 파일 객체의 파일크기를 가져오는 기능을 제공하는 API 함수입니다. | |
| getAttributeEditedTime | getAttributeEditedTime | 파일 객체의 마지막으로 수정된 시간을 가져오는 기능을 제공하는 API 함수입니다. | |
| getFileList | getFileList | 폴더의 내용물을 가져오는 기능을 제공하는 API 함수입니다. | |
| getFileListEx | getFileListEx | 폴더의 내용물을 가져오는 기능을 제공하는 API 함수입니다. | |
| CreateCNCFile | CreateCNCFile | NC파일을 생성하는 기능을 제공하는 API 함수입니다. | |
| CreateCNCFolder | CreateCNCFolder | NC 폴더를 생성하는 기능을 제공하는 API 함수입니다. | |
| CNCFileRename | CNCFileRename | 파일 혹은 폴더 명칭을 수정하는 기능을 제공하는 API 함수입니다. | |
| CNCFileCopy | CNCFileCopy | 파일을 복사하는 기능을 제공하는 API 함수입니다. | |
| CNCFileMove | CNCFileMove | 파일을 이동시키는 기능을 제공하는 API 함수입니다.킵니다. | |
| CNCFileDelete | CNCFileDelete | 파일 혹은 폴더를 삭제하는 기능을 제공하는 API 함수입니다. | |
| CNCFileDeleteAll | CNCFileDeleteAll | 지정한 폴더에 있는 모든 폴더와 파일을 삭제하는 기능을 제공하는 API 함수입니다. | |
| CNCFileExecute | CNCFileExecute | 제어기 NC default 경로에 있는 가공 프로그램을 실행 프로그램으로 설정합니다. | |
| CNCFileExecuteExtern | CNCFileExecuteExtern | 제어기 NC default 경로 이외의 경로에 있는 가공 프로그램을 실행 프로그램으로 설정합니다. | |
| UploadFile | UploadFile | NC 지정 경로에 Local nc 파일을 upload 합니다. | |
| DownloadFile | DownloadFile | Local 지정 경로에 nc 파일을 download 합니다. | |
| Log API | sendLog | sendLog | Platform에 Log를 추가하는 API 함수 입니다. |
| sendLogEx | sendLogEx | Platform에 Log를 추가하는 API 함수 입니다. ( LOGLEVEL 지정 ) | |
| Event Handler & callback | regist_callback | regist_callback | callback 함수를 등록하는 API 함수 입니다 |
| OnEvent_GetData | - | 다른 App에서 getData를 요청할 때 발생하는 Event | |
| OnEvent_UpdateData | - | 다른 App에서 updateData를 요청할 때 발생하는 Event | |
| OnEvent_InsertData | - | 다른 App에서 insertData를 요청할 때 발생하는 Event | |
| OnEvent_DeleteData | - | 다른 App에서 deleteData를 요청할 때 발생하는 Event | |
| OnEvent_Broadcast | - | 다른 App에서 Broadcast명령을 요청할 때 발생하는 Event | |
| OnEvent_ControlApp | - | 다른 App에서 controlApp을 요청할 때 발생하는 Event | |
| OnEvent_Show | - | 다른 App에서 controlApp/Show를 요청할 때 발생하는 Event | |
| OnEvent_Create | - | 다른 App에서 controlApp/Create를 요청할 때 발생하는 Event | |
| OnEvent_Run | - | 다른 App에서 controlApp 실행을 요청할 때 발생하는 Event | |
| OnEvent_Stop | - | 다른 App에서 controlApp 정지를 요청할 때 발생하는 Event | |
| OnEvent_Pause | - | 다른 App에서 controlApp 일시 정지를 요청할 때 발생하는 Event | |
| OnEvent_Destroy | - | 다른 App에서 controlApp 종료를 요청할 때 발생하는 Event | |
| OnEvent_Hide | - | 다른 App에서 controlApp/Hide를 요청할 때 발생하는 Event | |
| OnEvent_GetDataAsync | - | 다른 App에서 getDataAsync를 요청할 때 발생하는 Event | |
| OnEvent_GetDataAsyncResult | - | 다른 App에서 getDataAsyncResult를 요청할 때 발생하는 Event | |
| OnEvent_SubscribData | - | App에서 subscribeData를 요청할 때 발생하는 Event | |
| OnEvent_RegistSubscribeData | - | App에서 RegistsubscribeData를 요청할 때 발생하는 Event | |
| OnEvent_UnregistSubscribeData | - | App에서 UnregistSubscribeData를 요청할 때 발생하는 Event | |
| OnEvent_ClearSubscribeData | - | App에서 ClearSubscribeData를 요청할 때 발생하는 Event | |
| OnEvent_DeliveryFile | - | App 간 DeliveryFile 관련 실행시 발생하는 Event | |
| OnEvent_TimeSeriesData | - | 다른 App에서 TimeSeriesData 관련 실행시 발생하는 Event | |
| Xtrace API | AddTraceMsg | AddTraceMsg | “XTrace” 클래스의 실시간 로그를 기록하는 함수입니다 |
| TimeSeries API | startTimeSeries | startTimeSeries | 시계열 데이터 수집을 시작하는 API 함수 입니다. |
| endTimeSeries | endTimeSeries | 시계열 데이터 수집을 종료하는 API 함수 입니다. | |

Table 13 – API List 

---

### 7.2 TORUS Platform User API 설명
7. TORUS Platform User API 

---

#### 7.2.1 API Initialize
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 Application에 명령 또는 데이터를 전달할 수 있는 API를 설명합니다. 

---

##### 7.2.1.1 Initialize
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.1 API Initialize 

- API 함수 설명 “ Initialize ” API 함수는 플랫폼에 해당 Application을 최종적으로 사용 등록하는 함수 입니다.

- API 함수 원형 Initialize API함수의 원형은 다음과 같습니다.
C++

| int Initialize( void ); |
| ----------------------- |

| CApi* Initialize( __IN const char* appid, __IN const char* appname, ); |
| ---------------------------------------------------------------------- |

| CApi* Initialize( __IN GUID appid, __IN const char* appname, ); |
| --------------------------------------------------------------- |

| CApi* Initialize( __IN GUID appid, __IN const char* appname, __IN const char* strMapFilePath ); |
| ----------------------------------------------------------------------------------------------- |

C#

| int Initialize( __IN Guid appid, __IN string appname, ); |
| -------------------------------------------------------- |

| int Initialize( __IN Guid appid, __IN string appname, __IN string strMapFilePath ); |
| ----------------------------------------------------------------------------------- |

파라메터 Initialize API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| appid | App의 유일하게 식별 하는 GUID를 입력합니다. |
| appname | App이름을 입력한다. |
| strMapFilePath | 비가공장비 연결, TORUS Platform 구동 산업용 통신 서버 연결 혹은 NC internal PLC 데이터 액세스을 위해 설정한 mapping table이 저장된 파일 이름 주의: 파일 이름만 입력합니다. 파일은 App이 설치된 경로에 있어야 합니다. 주의: mapping file 작성법은 '3.1.5 비 가공장비 어드레스 매핑 테이블 작성' 혹은 '3.1.6 NC internal PLC 어드레스 매핑 테이블 작성'을 참고하시기 바랍니다. |

- 반환 값
1) 파라미터 void 타입 ( C++ ) 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code) 2) 파라미터 void 타입이 아닌 경우 *  C++ 의 경우 반환 값은 Platform User 라이브러리 객체 입니다. - null : 객체 생성 실패 *  C# 의 경우 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 객체 생성 성공 - 그 외 반환 값: 실패(Error code)
- 사용법 및 주의사항 Initialize는 mgrApplication에서 App 등록 여부를 판단 후 실행되므로, 등록 정보 파일의 정보와 Initialize 정보가 일치 해야 합니다.
즉,  Initialize 함수의 Guid와  등록 정보 파일의 "App ID", Initialize 함수의 appname과 등록 정보 파일의 "App Name"이 동일해야 합니다. 또한, 등록정보 파일은 Platform  실행전 Platform실행 경로\application 폴더에 미리 저장되어 있어야 합니다. Application 등록 정보 파일 작성은 “3 .1 Application 등록 정보 파일 ” 항목을 참고하면 됩니다. 예제 C++
- 예제 1

| { CApi* api = CApi::Get("5A205E01-4CB4-427A-86DA-D407E74857F5", "ConsoleDataAccess"); int resulta = api->initialize(); if (resulta != 0) exit(0); api->GuiLoaded(); } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- 예제 2

| { CApi* api = CApi::initialize("36B2E85E-486A-403B-9C5C-E71F87CFB4DC", "App Sample"); if (api != NULL) api->GuiLoaded(); } |
| -------------------------------------------------------------------------------------------------------------------------- |

- 예제 3

| { CApi* api = CApi::initialize(new Guid("36B2E85E-486A-403B-9C5C-E71F87CFB4DC", "App Sample"); if (api != NULL) api->GuiLoaded(); } |
| ----------------------------------------------------------------------------------------------------------------------------------- |

- 예제 4

| { CApi* api = CApi::initialize(new Guid("36B2E85E-486A-403B-9C5C-E71F87CFB4DC", "App Sample", "DevMapFilePath.xml"); if (api != NULL) api->GuiLoaded(); } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#
- 예제

| { int iRst = Api.Initialize(new Guid("36B2E85E-486A-403B-9C5C-E71F87CFB4DC", "App Sample"); if (iRst != 0) { MessageBox.Show("initialize error"); return; } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- 예제

| { int iRst = Api.Initialize(new Guid("36B2E85E-486A-403B-9C5C-E71F87CFB4DC", "App Sample", "dataMapFile.xml"); if (iRst != 0) { MessageBox.Show("initialize error"); return; } } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

#### 7.2.2 Data Access API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

CNC Data Read/Write를 위한 API 설명 입니다. 

---

##### 7.2.2.1 getData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getData ” API 함수는 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 getData API함수의 원형은 다음과 같습니다.
C++ (단일 데이터를 읽어오는 함수)

| int getData( __IN const char* address, __IN const char* filter, __OUT ITEM_HANDLE result, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

(다수의  데이터를 읽어오는 함수)

| int getData( __IN const char** address, __IN const char** filter, __IN int arrcnt, __OUT ITEM_HANDLE result, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| arrcnt | 다수의 데이터를 읽어 오는 함수에서 address & filter 수량 |
| result | 주소로 지정한 Machine Data Model의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 arrcnt 만큼의 배열 data 가 전달됨. |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# (단일 데이터를 읽어오는 함수)

| int getData( __IN string address, __IN string filter, __OUT out Item result, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- |

(다수의  데이터를 읽어오는 함수)

| int getData( __IN string[] address, __IN string[] filter, __OUT out Item[] result, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터

| Parameter 이름 | 설명 |
| ------------ | ----------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| result | 주소로 지정한 Machine Data Model의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 배열 data 가 전달됨. |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 getData API 함수는 주소로 지정한 데이터의 값을 읽어오는 함수로, Application에서 제공하는 데이터뿐만 아니라 Machine Data Model의 데이터도 읽어올 수 있습니다. 데이터 주소 입력 형식은 “ 2.2 Data주소 체계 기본 사용 규칙 ” 항목을 참고하면 됩니다.

- 예제
C++

| … commandTable table[] = { {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=1"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=2"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=3"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=4"}, {CMD_END,}, }; //단일데이터 Get void getData(CApi* api, int index) { Item item; api->getData(table[index].address, table[index].filter, &item); const Value& a = item["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getData] value[%d] = %.3f\n", i, a[i].GetDouble()); //index++; } //복수데이터 Get void getArrayData(CApi* api, int index) { #define ARRAY_COUNT 4 Item item[ARRAY_COUNT]; char** address = new char* [ARRAY_COUNT]; char** filter = new char* [ARRAY_COUNT]; for (int i = 0; i < ARRAY_COUNT; i++) { address[i] = new char[MAX_PATH]; filter[i] = new char[MAX_PATH]; memset(address[i], 0, MAX_PATH); memset(filter[i], 0, MAX_PATH); strcpy(address[i], table[i].address); strcpy(filter[i], table[i].filter); } api->getData((const char**)address, (const char**)filter, ARRAY_COUNT, (ITEM_HANDLE)item); for (int i = 0; i < ARRAY_COUNT; i++) { const Value& a = item[i]["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getArrayData] value = %.3f", a[i].GetDouble()); //index++; } printf("\n"); for (int i = 0; i < ARRAY_COUNT; i++) { delete address[i]; delete filter[i]; } delete[] address; delete[] filter; } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| //단일데이터 Get int iRst; Item result; double dValue; iRst = Api.getData(“data://machine/channel/axis/machinePosition”, “channel=1&axis=1”, out Result, true ); if (iRst) { // Error 처리 } else { Items resultArr = (Items)result; List<Item> val = (List<Item>)resultArr[0].GetValue(); object obj = val[0].GetValue(); if (obj.GetType() == typeof(double)) { data = (double)obj; } … } //복수 데이터 Get List<string> addr = new List<string>(); List<string> filter = new List<string>(); Item[] result; addr.Add("data://machine/channel/axis/workposition"); filter.Add("machine=1&channel=1&axis=1-3"); addr.Add("data://machine/channel/axis/machineposition"); filter.Add("machine=1&channel=1&axis=1-3"); int res = Api.getData(addr.ToArray(), filter.ToArray(), out result, true); string strresult = ""; if (result != null) { foreach (Item item in result) { strresult += "\r\n" + item.ToString(); } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.2.2 getData ( 주기 다양화 )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getData ” API 함수는 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다.
"getData" API 함수에서 확장된 함수로 Machine Data Model에 등록된 address의 data 값 업데이트 주기를 설정하는 기능이 추가된 API 함수 입니다.
- API 함수 원형 getData API함수의 원형은 다음과 같습니다.
C++ (주기 설정 단일 데이터를 읽어오는 함수)

| int getData( __IN const char* address, __IN const char* filter, __OUT ITEM_HANDLE result, __IN PERIOD_LEVEL level, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

(주기 설정 다수의  데이터를 읽어오는 함수)

| int getData( __IN const char** address, __IN const char** filter, __IN int arrcnt, __OUT ITEM_HANDLE result, __IN PERIOD_LEVEL level, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| arrcnt | 다수의 데이터를 읽어 오는 함수에서 address & filter 수량 |
| result | 주소로 지정한 Machine Data Model의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 arrcnt 만큼의 배열 data 가 전달됨. |
| level | PERIOD_LEVEL 에서 통신 주기 레벨을 설정 |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# (주기 설정 단일 데이터를 읽어오는 함수)

| int getData( __IN string address, __IN string filter, __OUT out Item result, __IN PERIOD_LEVEL level, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

(주기 설정 다수의  데이터를 읽어오는 함수)

| int getData( __IN string[] address, __IN string[] filter, __OUT out Item[] result, __IN PERIOD_LEVEL level, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 배열 data 가 전달됨. |
| level | PERIOD_LEVEL 에서 통신 주기 레벨을 설정 |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값 PERIOD_LEVEL 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------- | --- | --------------------------------------------------------------------------------------------- |
| PERIOD_LV1 | 0 | getData API 함수의 'address' 파라메터에 등록된 address의 data 값을 매 통신 주기마다 Machine Data Model로부터 업데이트 |
| PERIOD_LV2 | 1 | getData API 함수의 'address' 파라메터에 등록된 address의 data 값을 통신 주기 5회에 1번 Machine Data Model로부터 업데이트 |
| PERIOD_LV3 | 2 | getData API 함수의 'address' 파라메터에 등록된 address의 data 값을 통신 주기 10회에 1번 Machine Data Model로부터 업데이트 |
| PERIOD_LV4 | 3 | getData API 함수의 'address' 파라메터에 등록된 address의 data 값을 통신 주기 15회에 1번 Machine Data Model로부터 업데이트 |
| PERIOD_LV5 | 4 | getData API 함수의 'address' 파라메터에 등록된 address의 data 값을 통신 주기 20회에 1번 Machine Data Model로부터 업데이트 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 getData API 함수는 주소로 지정한 데이터의 값을 읽어오는 함수로, Application에서 제공하는 데이터뿐만 아니라 Machine Data Model의 데이터도 읽어올 수 있습니다. 데이터 주소 입력 형식은 “ 2.2 Data주소 체계 기본 사용 규칙 ” 항목을 참고하면 됩니다.

- 예제
C++

| … commandTable table[] = { {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=1"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=2"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=3"}, {CMD_ON, "data://machine/channel/axis/machineposition", "channel=1&axis=4"}, {CMD_END,}, }; void getData_Period(CApi* api, int index) { Item item[3]; api->getData(table[0].address, table[0].filter, &item[0], PERIOD_LV1); api->getData(table[1].address, table[1].filter, &item[1], PERIOD_LV3); api->getData(table[2].address, table[2].filter, &item[2], PERIOD_LV5); for (int i = 0; i < 3; i++) { const Value& a = item[i]["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getData_Period] value = %.3f / ", a[i].GetDouble()); //index++; } printf("\n"); } //복수데이터 Get void getDataArray_Period(CApi* api, int index) { #define ARRAY_COUNT 3 Item item[ARRAY_COUNT]; char** address = new char* [ARRAY_COUNT]; char** filter = new char* [ARRAY_COUNT]; for (int i = 0; i < ARRAY_COUNT; i++) { address[i] = new char[MAX_PATH]; filter[i] = new char[MAX_PATH]; memset(address[i], 0, MAX_PATH); memset(filter[i], 0, MAX_PATH); strcpy(address[i], table[i].address); strcpy(filter[i], table[i].filter); } api->getData((const char**)address, (const char**)filter, ARRAY_COUNT, (ITEM_HANDLE)item, PERIOD_LV3, false); for (int i = 0; i < ARRAY_COUNT; i++) { const Value& a = item[i]["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getDataArray_Period] value = %.3f / ", a[i].GetDouble()); //index++; } printf("\n"); for (int i = 0; i < ARRAY_COUNT; i++) { delete address[i]; delete filter[i]; } delete[] address; delete[] filter; } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| //단일데이터 Get int iRst; Item result; double dValue; iRst = Api.getData(“data://machine/channel/axis/machinePosition”, “channel=1&axis=1”, out Result, PERIOD_LEVEL.PERIOD_LV1, true ); if (iRst) { // Error 처리 } else { Items resultArr = (Items)result; List<Item> val = (List<Item>)resultArr[0].GetValue(); object obj = val[0].GetValue(); if (obj.GetType() == typeof(double)) { data = (double)obj; } … } //복수 데이터 Get List<string> addr = new List<string>(); List<string> filter = new List<string>(); Item[] result; addr.Add("data://machine/channel/axis/workposition"); filter.Add("machine=1&channel=1&axis=1-3"); addr.Add("data://machine/channel/axis/machineposition"); filter.Add("machine=1&channel=1&axis=1-3"); int res = Api.getData(addr.ToArray(), filter.ToArray(), out result, PERIOD_LEVEL.PERIOD_LV3, true); string strresult = ""; if (result != null) { foreach (Item item in result) { strresult += "\r\n" + item.ToString(); } } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.3 getDataEx
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getDataEx ” API 함수는 지정한 데이터의 값을 읽어오는 기능을 제공하는 API 함수 입니다.
"getData" API 함수에서 확장된 함수로 사용자 Application 의 Hide 상태일 때 통신 여부를 설정할 수 있도록 제공된 API 함수 입니다.
- API 함수 원형 getDataEx API함수의 원형은 다음과 같습니다.
C++ ( 단일 데이터를 읽어오는 함수)

| int getDataEx( __IN const char* address, __IN const char* filter, __OUT ITEM_HANDLE result, __IN PERIOD_LEVEL level, __IN bool bAppHideOperable = false, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

( 다수의  데이터를 읽어오는 함수)

| int getDataEx( __IN const char** address, __IN const char** filter, __IN int arrcnt, __OUT ITEM_HANDLE result, __IN PERIOD_LEVEL level, __IN bool bAppHideOperable = false, __IN bool direct = true, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- 파라메터 getDataEx API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| arrcnt | 다수의 데이터를 읽어 오는 함수에서 address & filter 수량 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 arrcnt 만큼의 배열 data 가 전달됨. |
| level | PERIOD_LEVEL 에서 통신 주기 레벨을 설정 |
| bAppHideOperable | App Hide 일때 통신 여부 설정 ( 옵션. “false” 인 경우 - hide 상태 일때 통신 안함 ) |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# ( 단일 데이터를 읽어오는 함수)

| int getDataEx( __IN string address, __IN string filter, __OUT out Item result, __IN PERIOD_LEVEL level, __IN bool bAppHideOperable = false, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

( 다수의  데이터를 읽어오는 함수)

| int getDataEx( __IN string[] address, __IN string[] filter, __OUT out Item[] result, __IN PERIOD_LEVEL level, __IN bool bAppHideOperable = false, __IN bool direct = true, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getDataEx API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ---------------- | ------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 배열 data 가 전달됨. |
| level | COMM_PERIOD 에서 통신 주기 레벨을 설정 |
| bAppHideOperable | App Hide 일때 통신 여부 설정 ( 옵션. “false” 인 경우 - hide 상태 일때 통신 안함 ) |
| direct | 옵션. “true”인 경우 비 주기 데이터 송수신 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 getData API 함수는 주소로 지정한 데이터의 값을 읽어오는 함수로, Application에서 제공하는 데이터뿐만 아니라 Machine Data Model의 데이터도 읽어올 수 있습니다. 데이터 주소 입력 형식은 ' 1.3.2 Data주소 체계 기본 사용 규칙' 항목을 참고하면 됩니다.

- 예제
C++

| … //단일데이터 App Hide 호환 void getDataEX_Period(CApi* api, int index) { Item item[3]; api->getDataEX(table[0].address, table[0].filter, &item[0], PERIOD_LV1, true); api->getDataEX(table[1].address, table[1].filter, &item[1], PERIOD_LV3, true); api->getDataEX(table[2].address, table[2].filter, &item[2], PERIOD_LV5, true); for (int i = 0; i < 3; i++) { const Value& a = item[i]["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getDataEX_Period] value = %.3f / ", a[i].GetDouble()); //index++; } printf("\n"); } //복수데이터 App Hide 호환 void getDataArrayEX_Period(CApi* api, int index) { #define ARRAY_COUNT 3 Item item[ARRAY_COUNT]; char** address = new char* [ARRAY_COUNT]; char** filter = new char* [ARRAY_COUNT]; for (int i = 0; i < ARRAY_COUNT; i++) { address[i] = new char[MAX_PATH]; filter[i] = new char[MAX_PATH]; memset(address[i], 0, MAX_PATH); memset(filter[i], 0, MAX_PATH); strcpy(address[i], table[i].address); strcpy(filter[i], table[i].filter); } api->getDataEX((const char**)address, (const char**)filter, ARRAY_COUNT, (ITEM_HANDLE)item, PERIOD_LV3, false); for (int i = 0; i < ARRAY_COUNT; i++) { const Value& a = item[i]["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getDataArrayEX_Period] value = %.3f / ", a[i].GetDouble()); //index++; } printf("\n"); for (int i = 0; i < ARRAY_COUNT; i++) { delete address[i]; delete filter[i]; } delete[] address; delete[] filter; } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| //단일데이터 Get int iRst; Item result; double dValue; iRst = Api.getDataEx(“data://machine/channel/axis/machinePosition”, “channel=1&axis=1”, out Result, PERIOD_LEVEL.PERIOD_LV1, true, true ); if (iRst) { // Error 처리 } else { Items resultArr = (Items)result; List<Item> val = (List<Item>)resultArr[0].GetValue(); object obj = val[0].GetValue(); if (obj.GetType() == typeof(double)) { data = (double)obj; } … } //복수 데이터 Get List<string> addr = new List<string>(); List<string> filter = new List<string>(); Item[] result; addr.Add("data://machine/channel/axis/workposition"); filter.Add("machine=1&channel=1&axis=1-3"); addr.Add("data://machine/channel/axis/machineposition"); filter.Add("machine=1&channel=1&axis=1-3"); int res = Api.getDataEx(addr.ToArray(), filter.ToArray(), out result, PERIOD_LEVEL.PERIOD_LV3, true, true); string strresult = ""; if (result != null) { foreach (Item item in result) { strresult += "\r\n" + item.ToString(); } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.2.4 getDataAsync
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getDataAsync ” API 함수는 비동기로 Data를 읽어오는 기능을 제공하는 API 함수입니다.
(C++)" GETDATAASYNCRESULT " callback 함수를 등록하여 호출 시 수신 데이터 처리가 가능합니다. (C#)" GETDATAASYNCRESULT " 이벤트를 이용해 수신 데이터 처리가 가능합니다.
- API 함수 원형
getDataAsync API함수의 원형은 다음과 같습니다. C++

| int getDataAync( __IN const char* address, __IN const char* filter, ); |
| ---------------------------------------------------------------------- |

C#

| int getDataAync( __IN string address, __IN string filter, ); |
| ------------------------------------------------------------ |

파라메터 getDataAsync API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 비동기 통신 요청시 수신 데이터 없이 반환되고, 실제 수신 데이터는 "GETDATAASYNCRESULT" callback 함수가 호출됩니다.

- 예제
C++

| int onGetDataAsyncResult(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); return 0; } int main() { .................. api->regist_callback(CALLBACK_TYPE::CALLBACK_GETDATAASYNCRESULT, onGetDataAsyncResult); int res = api->getDataAsync("data://SampleHmi2018R/asyncdata", "") ........ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| void Api_OnEvent_GetDataAsyncResult(ApiEventArgs e) { Item item = e.item; Item result = (Item)item.find("result"); string msg = result.GetValueString("result"); m_asyncData = msg; Database.AddLog("SampleHmi2018L", 1, "비동기 데이터 결과 : " + msg); } int main() { // 이벤트 등록 Api.OnEvent_GetDataAsyncResult += Api_OnEvent_GetDataAsyncResult; int iRst = Api.getDataAsync("data://SampleHmi2018R/asyncdata", ""); if (iRst) { // Error 처리 } else { // 완료 } } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.5 getDataAsyncResult
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getDataAsyncResult ” API 함수는 他 App에서 getDataAsync를 요청했을때 결과값을 보내는 API함수입니다.

- API 함수 원형 getDataAsyncResult API함수의 원형은 다음과 같습니다.
C++

| int getDataAyncResult( __IN const char* address, __IN ITEM_HANDLE result, ); |
| ---------------------------------------------------------------------------- |

C#

| int getDataAyncResult( __IN string address, __IN Item result, ); |
| ---------------------------------------------------------------- |

파라메터 getDataAsyncResult API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 -

- 예제
C++ 예제

| int onGetDataAsync(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); Item* item = new Item(); item->Parse("{\"value\":["Test"]}"); api->getDataAsyncResult("data://CallerSample/result", item); return 0; } int main() { ....... api->regist_callback(CALLBACK_TYPE::CALLBACK_GETDATAASYNC, onGetDataAsync); ........ } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

예제 ( getDataAsyncResult 함수 호출 없이 Caller의 getDataAsync 호출에 대한 결과값을 반환하는 방법 )

| int onGetDataAsync(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); Item* item = new Item(); item->Parse("{\"value\":[1]}"); const char* str = "T1D1G91G54X0.Y0.Z0.G01Z-19.00F2000"; int memsize = strlen(str); char* mem = new char[memsize+1]; strcpy(mem, str); *result = mem; //api->getDataAsyncResult(command, (ITEM_HANDLE)item); //api->getDataAsyncResult("data://appTester", (ITEM_HANDLE)item); return 0; } int main() { ....... api->regist_callback(CALLBACK_TYPE::CALLBACK_GETDATAASYNC, onGetDataAsync); ........ } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C# 예제

| int async_count = 0; DateTime start = DateTime.Now; int main() { // 이벤트 등록 Api.OnEvent_GetDataAsync += Api_OnEvent_GetDataAsync; Timer m_ASyncTimer = new Timer(); m_ASyncTimer.Interval = 30; m_ASyncTimer.Tick += m_ASyncTimer_Tick; m_ASyncTimer.Start(); } void m_ASyncTimer_Tick(object sender, EventArgs e) { if (async_count <= 0) return; TimeSpan sp = DateTime.Now - start; if(sp.Seconds < async_count) return; async_count = 0; ItemString item = new ItemString(); item.Value = "비동기 데이터 전달"; if (data_async != null) { Api.getDataAsyncResult(data_async, item); MessageBox.Show("비동기 데이터(RECV) - 완료"); } } ApiEventArgs data_async; void Api_OnEvent_GetDataAsync(ApiEventArgs e) { async_count = 3; start = DateTime.Now; data_async = e; } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- 예제  ( getDataAsyncResult 함수 호출 없이 Caller의 getDataAsync 호출에 대한 결과값을 반환하는 방법 )

| int async_count = 0; DateTime start = DateTime.Now; int main() { // 이벤트 등록 Api.OnEvent_GetDataAsync += Api_OnEvent_GetDataAsync; Timer m_ASyncTimer = new Timer(); m_ASyncTimer.Interval = 30; m_ASyncTimer.Tick += m_ASyncTimer_Tick; m_ASyncTimer.Start(); } void m_ASyncTimer_Tick(object sender, EventArgs e) { if (async_count <= 0) return; TimeSpan sp = DateTime.Now - start; if(sp.Seconds < async_count) return; async_count = 0; ItemString item = new ItemString(); item.Value = "비동기 데이터 전달"; //if (data_async != null) //{ // Api.getDataAsyncResult(data_async, item); // MessageBox.Show("비동기 데이터(RECV) - 완료"); //} } ApiEventArgs data_async; void Api_OnEvent_GetDataAsync(ApiEventArgs e) { async_count = 3; start = DateTime.Now; data_async = e; ItemTextParser parser = new ItemTextParser(); ItemString item = new ItemString(); item.Value = "비동기 데이터 전달"; e.resultdata = item; } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.6 subscribeData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ subscribeData ” API 함수는 구독할 데이터를 Manager에 등록하는 함수 입니다.

- API 함수 원형 subscribeData API함수의 원형은 다음과 같습니다.
C++ (구독할 데이터만 등록하는  함수)

| int subscribeData( __IN const char* address, __IN const char* filter, ); |
| ------------------------------------------------------------------------ |

(구독할 데이터 등록하고 구독 Object의 ID를 반환 받는 함수).

| int subscribeData( __IN const char* address, __IN const char* filter, __OUT int* objectID ); |
| -------------------------------------------------------------------------------------------- |

C# (구독할 데이터만 등록하는  함수)

| int subscribeData( __IN string address, __IN string filter, ); |
| -------------------------------------------------------------- |

(구독할 데이터 등록하고 구독 Object의 ID를 반환 받는 함수)

| int subscribeData( __IN string address, __IN string filter, __OUT out int objectID ); |
| ------------------------------------------------------------------------------------- |

파라메터 subscribeData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| objectID | address/filter로 등록된 구독할 데이터의 ID |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
등록한 데이터의 값이 변경되었을 때 발생한 C++은  " SubscribeData" callback 함수 호출을  통해, C# 은 " OnEvent_SubscribeData" 이벤트를 통해 값을 전달 받을수 있습니다. 값이 변경되지 않을 경우는 이벤트가 발생하지 않습니다. unsubscribeData를 이용하여 구독을 해제하기 전까지는 구독된 데이터가 해제되지 않습니다. App을 종료하기 전 구독을 해제하여 주시기 바랍니다. 이벤트 핸들러와 관련된 사항은 ' 7.2.8 Event Handler' 항목을 참고하시면 됩니다.
- 예제
C++

| int OnSubscribeData(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); return 0; } int main() { .................. api->regist_callback(CALLBACK_TYPE::CALLBACK_ON_SUBSCRIBEDATA, OnSubscribeData); int res = api->subscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1"); ........ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |

예제 ( ObjectID )

| int OnSubscribeData(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); return 0; } int objectid; int main() { .................. api->regist_callback(CALLBACK_TYPE::CALLBACK_ON_SUBSCRIBEDATA, OnSubscribeData); int res = api->subscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1", &objectid); ........ } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |

C#

| // 이벤트 핸들러 void Api_OnEvent_SubscribeData(ApiEventArgs e) { Item item = e.item; Item result = (Item)item.find("result"); Item nameitem = result.find("name"); if (nameitem != null) { string name = nameitem.GetValueString("name"); if (name == "machineposition") { Item value = result.find("value"); double val = value.GetValueDouble("value"); Item axisval = result.find("axis"); int axis = axisval.GetValueInt("axis"); machineposition[axis - 1] = val; } } Item dataitem = result.find("data"); if (dataitem != null) { string val = dataitem.GetValueString("data"); m_hotlinkData = val; } } int main() { // 이벤트 등록 Api.OnEvent_SubscribeData += Api_OnEvent_SubscribeData; Api.subscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1"); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

예제 ( ObjectID )

| // 이벤트 핸들러 void Api_OnEvent_SubscribeData(ApiEventArgs e) { Item item = e.item; Item result = (Item)item.find("result"); Item nameitem = result.find("name"); if (nameitem != null) { string name = nameitem.GetValueString("name"); if (name == "machineposition") { Item value = result.find("value"); double val = value.GetValueDouble("value"); Item axisval = result.find("axis"); int axis = axisval.GetValueInt("axis"); machineposition[axis - 1] = val; } } Item dataitem = result.find("data"); if (dataitem != null) { string val = dataitem.GetValueString("data"); m_hotlinkData = val; } } public int objectid = 0; int main() { // 이벤트 등록 Api.OnEvent_SubscribeData += Api_OnEvent_SubscribeData; Api.subscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1", out objectid); } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.7 subscribeDataResult
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ subscribeDataResult ” API 함수는 구독 요청받는 데이터의 변경을 통보하는 API 함수입니다. 이 함수가 실행되면 대상 App에서 " OnEvent_SubscribeData" 이벤트가 발생합니다.

- API 함수 원형
subscribeDataResult API함수의 원형은 다음과 같습니다. C++

| int subscribeDataResult( __IN const char* address, __IN ITEM_HANDLE item, ); |
| ---------------------------------------------------------------------------- |

C#

| int subscribeDataResult( __IN string address, __IN Item item, ); |
| ---------------------------------------------------------------- |

파라메터 subscribeDataResult API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| item | address에 해당하는 Data를 포함하는 item |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 다른 App(B)이 나(A)에게 구독을 요청했을 때 RegistSubscribeData 이벤트가 발생합니다.
나(A)에게 발생된 이벤트를 통해 전달된 ApiEventArgs의 address에서 구독을 요청한 App을 확인 할 수 있습니다. subscribeDataResult 함수를 이용해 구독을 요청한 App에 변경된 데이터의 값을 통보해 주면 App(B)에 SubscribeData 이벤트가 발생하며, 구독 요청한 값을 전달 받습니다. 이벤트 핸들러와 관련된 사항은 ' 7.2.8 Event Handler' 항목을 참고하시면 됩니다.
- 예제
C++

| //App (B) - App2 int OnSubscribeData(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); char res[1024] = { 0, }; sprintf_s(res, "%s", (char*)result); printf_s("result = %s\n", res); return -1; } int main() { //구독 신청 api->regist_callback(CALLBACK_TYPE::CALLBACK_ON_SUBSCRIBEDATA, OnSubscribeData); api->subscribeData("data://app1/hotlink", ""); } //App (A) - App1 int count = 0; bool m_hotlink = false; int OnRegistSubscribeData(int evt, int cmd, const char* command, char** result) { m_hotlink = true; char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("command = %s\n", msg); char res[1024] = { 0, }; sprintf_s(res, "%s", (char*)result); printf_s("result = %s\n", res); return -1; } void TimerProc() { if (m_hotlink) { Item item; char strtemp[256] = { 0, }; sprintf_s(strtemp, "{\"data\":[%d]}", count++); item.Parse(strtemp); const char* addr = "data://app2/hotlink"; int res = api->subscribeDataResult(addr, &item); } } int main() { api->regist_callback(CALLBACK_TYPE::CALLBACK_ON_RESGIST_SUBSCRIBEDATA, OnRegistSubscribeData); while (true) { printf("test\n"); TimerProc(); Sleep(1000); } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| //App (B) - SampleHMI2018L { //구독 신청 Api.subscribeData("data://SampleHMI2018R/hotlink", ""); } string m_hotlinkData = ""; void Api_OnEvent_SubscribeData(ApiEventArgs e) { Item item = e.item; Item result = (Item)item.find("result"); Item nameitem = result.find("name"); if (nameitem != null) { string name = nameitem.GetValueString("name"); if (name == "machineposition") { Item value = result.find("value"); double val = value.GetValueDouble("value"); Item axisval = result.find("axis"); int axis = axisval.GetValueInt("axis"); machineposition[axis - 1] = val; } } Item dataitem = result.find("data"); if (dataitem != null) { string val = dataitem.GetValueString("data"); m_hotlinkData = val; } } //App (A) - SampleHMI2018R int count = 0; { Api.OnEvent_RegistSubscribeData += Api_OnEvent_RegistSubscribeData; } void Api_OnEvent_RegistSubscribeData(ApiEventArgs e) { Item item = e.item; if (e.address == "data://SampleHMI2018R/hotlink") { m_hotlink = true; } } void m_timerHotlink_Tick(object sender, EventArgs e) { if (m_hotlink) { ItemTextParser parser = new ItemTextParser(); Item item = parser.Parse("{\"data\":[" + (count++).ToString() + "]}"); string addr = "data://SampleHMI2018L/hotlink"; Api.subscribeDataResult(addr, item); } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| } |

---

##### 7.2.2.8 unsubscribeData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명
“ unsubscribeData ” API 함수는 구독 요청을 해제하는 API 함수입니다.
- API 함수 원형 unsubscribeData API함수의 원형은 다음과 같습니다.
C++ (address와 filter를 이용해 해제하는 함수)

| int unsubscribeData( __IN const char* address, __IN const char* filter, ); |
| -------------------------------------------------------------------------- |

(ObjectID를 이용해 해제하는 함수)

| int unsubscribeData( __IN int objectID ); |
| ----------------------------------------- |

C# (address와 filter를 이용해 해제하는 함수)

| int unsubscribeData( __IN string address, __IN string filter, ); |
| ---------------------------------------------------------------- |

(ObjectID를 이용해 해제하는 함수)

| int unsubscribeData( __IN int objectID ); |
| ----------------------------------------- |

파라메터 unsubscribeData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| ObjectID | 등록된 구독 데이터의 ID |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 구독 요청을 해제하면 상대방 App 에  UnregistSubscribeData callback 함수 호출이 발생하며, 함수 호출시 매개변수를 통해 해제한 App에 대한 정보를 확인 할수 있습니다.

- 예제
C++ 예제

| { int iRst = api->unsubscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1-3"); } |
| --------------------------------------------------------------------------------------------------------- |

예제 ( ObjectID )

| { int iRst = api->unsubscribeData(objectid); } |
| ---------------------------------------------- |

C# 예제

| { int iRst = Api.unsubscribeData("data://machine/channel/axis/machineposition", "channel=1&axis=1-3"); } |
| -------------------------------------------------------------------------------------------------------- |

예제 ( ObjectID 함수 )

| { int iRst = Api.unsubscribeData(objectid); } |
| --------------------------------------------- |

---

##### 7.2.2.9 subscribeDataClear
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ subscribeDataClear ” API 함수는 App에서 subscribeData로 등록한 Address를 모두 제거하는 API 함수입니다.

- API 함수 원형
subscribeDataClear API함수의 원형은 다음과 같습니다. C++

| int subscribeDataClear( void ); |
| ------------------------------- |

C#

| int subscribeDataClear( void ); |
| ------------------------------- |

파라메터 subscribeDataClear API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------- |
| void | 파라미터 없음 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 unsubscribe의 경우 특정  구독 데이터를 해제하는 기능이며, “ subscribeDataClear ” API 함수는 현재 App에서 구독을 신청한 모든 데이터를 해제하는 기능 입니다.
이벤트 핸들러와 관련된 사항은 ' 7.2.8 Event Handler' 항목을 참고하시면 됩니다.
- 예제
C++

| { int iRst = api->subscribeDataClear(); if(iRst) { // 실패 } else { // 성공 } } |
| --------------------------------------------------------------------------- |

C#

| { int iRst = Api.subscribeDataClear(); if(iRst) { // 실패 } else { // 성공 } } |
| -------------------------------------------------------------------------- |

---

##### 7.2.2.10 updateData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ updateData ” API 함수는 지정한 데이터의 값을 업데이트 하는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 updateData API함수의 원형은 다음과 같습니다.
C++ ( 단일  데이터를 업데이트 하는  함수 )

| int updateData( __IN const char* address, __IN const char* filter, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- |

( 다수 데이터를 업데이트 하는  함수 )

| int updateData( __IN const char** address, __IN const char** filter, __IN int arrcnt, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 updateData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------ |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| arrcnt | 다수의 데이터를 읽어 오는 함수에서 address & filter 수량 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 arrcnt 만큼의 배열 data 가 전달됨. |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# ( 단일 데이터를 업데이트 하는  함수 )

| int updateData( __IN string address, __IN string filter, __IN Item data, __OUT out Item result, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------- |

( 다수의  데이터를 업데이트 하는  함수 )

| int updateData( __IN string[] address, __IN string[] filter, __IN Item data, __OUT out Item[] result, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 updateData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 배열 data 가 전달됨. |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| { Item* item = new Item(); ITEM_HANDLE dataitem = new Item; ITEM_HANDLE resultitem = new Item; item->Parse("{\"layout\":\"full\"}"); dataitem = item; api->updateData("data://app/layout", "", dataitem, resultitem); //uservariable const char* address = "data://machine/variable"; char filter[255] = { 0, }; int start_index = 0;// 500; int end_index = 3;// 503; sprintf_s(filter, "machine=%d&channel=1&start=%d&end=%d", 1, start_index, end_index); const char* str = "{\"value\": [10, 20, 30, 40]}"; Item item; Item data; data.Parse(str); int res = api->updateData(address, filter, &data, &item); if (res != 0) printf("[setUserVariable] Error res = %d", res); } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item updateRes = null; string param = parser.Parse("{\"layout\":\"full\"}"); Api.updateData("data://app/layout", "", param, out updateRes); // App Data update // uservariable string address = "data://machine/variable"; int start_index = 500;// 500; int end_index = 503;// 503; string filter = "machine=1&channel=1&start=" + start_index + "&end=" + end_index; string str = "{\"value\": [10, 20, 30, 40]}"; ItemTextParser parser = new ItemTextParser(); Item data = parser.Parse(str); Item item = null; int iRst = Api.updateData(address, filter, data, out item); // NC Data update if (iRst != 0x00) MessageBox.Show("Error: updateData error!!"); } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.11 updateDataEx
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ updateDataEx ” API 함수는 지정한 데이터의 값을 업데이트 하는 기능을 제공하는 API 함수 입니다.
"updateData" API 함수에서 확장된 함수로 사용자 Application 의 Hide 상태일때 업데이트 여부를 설정할 수 있도록 제공된  API 함수 입니다.
- API 함수 원형 updateDataEx API함수의 원형은 다음과 같습니다.
C++ ( 단일 데이터를 업데이트 하는  함수 )

| int updateDataEx( __IN const char* address, __IN const char* filter, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN bool bAppHideOperable = false, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

( 다수의  데이터를 업데이트 하는  함수 )

| int updateDataEx( __IN const char** address, __IN const char** filter, __IN int arrcnt, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN bool bAppHideOperable = false, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 updateData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| arrcnt | 다수의 데이터를 읽어 오는 함수에서 address & filter 수량 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 arrcnt 만큼의 배열 data 가 전달됨. |
| bAppHideOperable | App Hide 일때 통신 여부 설정 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# ( 단일 데이터를 업데이트 하는  함수 )

| int updateDataEX( __IN string address, __IN string filter, __IN Item data, __OUT out Item result, __IN bool bAppHideOperable = false, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

( 다수의  데이터를 업데이트 하는  함수 )

| int updateDataEX( __IN string[] address, __IN string[] filter, __IN Item data, __OUT out Item[] result, __IN bool bAppHideOperable = false, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

파라메터 updateData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| address | Machine Data Model 이나 App이 제공하는 Data의 주소 |
| filter | 데이터베이스 내에서 원하는 데이터를 식별하기 위한 조건이나 filter. Query문을 완성하는 데 사용 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 Machine Data Model 내의 data 혹은 App이 제공하는 data의 값 단일 데이터의 경우 단일 data 가 전달되며, 다수의 데이터인 경우 배열 data 가 전달됨. |
| operable | App Hide 일때 통신 여부 설정 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| { Item* item = new Item(); ITEM_HANDLE dataitem = new Item; ITEM_HANDLE resultitem = new Item; item->Parse("{\"layout\":\"full\"}"); dataitem = item; api->updateData("data://app/layout", "", dataitem, resultitem, true, 10000); //uservariable const char* address = "data://machine/variable"; char filter[255] = { 0, }; int start_index = 0;// 500; int end_index = 3;// 503; sprintf_s(filter, "machine=%d&channel=1&start=%d&end=%d", 1, start_index, end_index); const char* str = "{\"value\": [10, 20, 30, 40]}"; Item item; Item data; data.Parse(str); int res = api->updateDataEX(address, filter, &data, &item, true, 10000); if (res != 0) printf("[setUserVariable] Error res = %d", res); } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item updateRes = null; string param = parser.Parse("{\"layout\":\"full\"}"); Api.updateDataEX("data://app/layout", "", param, out updateRes, false, 10000); / /uservariable string address = "data://machine/variable"; int start_index = 500;// 500; int end_index = 503;// 503; string filter = "machine=1&channel=1&start=" + start_index + "&end=" + end_index; string str = "{\"value\": [10, 20, 30, 40]}"; ItemTextParser parser = new ItemTextParser(); Item data = parser.Parse(str); Item item = null; int iRst = Api.updateDataEX(address, filter, data, out item, false, 10000); if (iRst != 0x00) MessageBox.Show("Error: updateData error!!"); } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.12 InsertData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ insertData ” API 함수는 새로운 데이터를 추가하는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 insertData API함수의 원형은 다음과 같습니다.
C++

| int insertData( __IN const char* address, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int insertData( __IN string address, __IN Item data, __OUT out Item result, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------- |

파라메터 insertData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| address | App이 제공하는 Data의 주소 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 data의 단일 데이터 값 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 Nc 통신 데이터의 경우는 적용되지 않습니다. 그러므로 Machine Data Model 내의 데이터를 사용할 수 없습니다.

- 예제
C++

| { ITEM_HANDLE InsertParam = new Item; ITEM_HANDLE resultitem = new Item; item->Parse(" {\"LevelName\":\"OperationManager\",\"LevelParam\":\"HMI_APP1\"} "); InsertParam = item; int res = api->insertData("data://security/userLevelProperty", InsertParam, resultitem); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item resultitem; Item InsertParam = parser.Parse(" {\"LevelName\":\"OperationManager\",\"LevelParam\":\"HMI_APP1\"} "); int res = Api.insertData("data://security/userLevelProperty", InsertParam, out resultitem); } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.13 deleteData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ deleteData ” API 함수는 기존 데이터를 삭제하는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 deleteData API함수의 원형은 다음과 같습니다.
C++

| int deleteData( __IN const char* address, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int deleteData( __IN string address, __IN Item data, __OUT out Item result, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------- |

파라메터 deleteData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| address | App이 제공하는 Data의 주소 |
| data | address에 해당하는 데이터 값 |
| result | 주소로 지정한 data의 값 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 Nc 통신 데이타의 경우는 적용되지 않습니다. 그러므로 Machine Data Model 내의 데이터를 사용할 수 없습니다.

- 예제
C++

| { ITEM_HANDLE DeleteParam = new Item; ITEM_HANDLE resultitem = new Item; item->Parse("{\"appGUID\":\"36B2E85E-486A-403B-9C5C-E71F87CFB4DC\"}"); DeleteParam = item; int res = api->deleteData("data://security/userLevelProperty", DeleteParam, resultitem); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item resultitem; Item DeleteParam = parser.Parse("{\"appGUID\":\"36B2E85E-486A-403B-9C5C-E71F87CFB4DC\"}"); int res = Api.deleteData("data://security/appAccount", DeleteParam, out resultitem); } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.14 getToolOffsetData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getToolOffsetData ” API 함수는 설정된 Tool offset data를 가져오는 API 함수 입니다.

- API 함수 원형 getToolOffsetData API함수의 원형은 다음과 같습니다.
C++

| int getToolOffsetData( __IN const char* channel, __IN const char* number, __IN const char* type, __IN bool direct, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int getToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN bool direct, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int getToolOffsetData( __IN string channel, __IN string number, __IN string type, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int getToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getToolOffsetData API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 계통 번호 |
| number | Tool Offset 번호 |
| type | Tool Offset 타입 번호 |
| direct | 주기/비주기 통신 옵션 |
| result | Tool offset data 반환값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

type 파라미터에 입력 가능한 값은 다음과 같습니다.

| type | FANUC | MITSUBISHI | | |
| ---- | ---------------------- | ---------- | ---------------------- | ---------- |
| 밀링 | 선반 | 밀링 | 선반 | |
| 0 | | T | | T |
| 1 | Tool length/geometry | Geometry X | Tool length/geometry | Geometry X |
| 2 | Tool length/wear | Wear X | Tool length/wear | Wear X |
| 3 | Cutter radius/geometry | Geometry Y | Cutter radius/geometry | Geometry Y |
| 4 | Cutter radius/wear | Wear Y | Cutter radius/wear | Wear Y |
| 5 | | Geometry Z | | Geometry Z |
| 6 | | Wear Z | | Wear Z |
| 7 | | Geometry R | | Geometry R |
| 8 | | Wear R | | Wear R |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
SIEMENS에서는 해당 함수와 대응 되는 기능이 존재하지 않습니다. 해당 기능 사용시 오류 코드가 반환 됩니다.
- 예제
C++

| { int iRst = 0xFF; Item rstItem; iRst = m_api->getToolOffsetData("1", "7-9", "3", true, &rstItem); if (iRst == 0x00) { const Value& a = rstItem["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getData] value[%d] = %.3f\n", i, a[i].GetDouble()); //index++; } else MessageBox.Show("Test is Fail!!"); } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { int iRst = 0xFF; Item rstItem; iRst = Api.getToolOffsetData("1", "7-9", "3", true, out rstItem); if (iRst == 0x00) { List<Item> tempData = (List<Item>)rstItem.GetValue(); Item tmpItem = tempData[0]; double[] dbArrValue = tmpItem.GetArrayDouble("value"); MessageBox.Show("Test is Success!! value1=" + dbArrValue[0].ToString() + " value2=" + dbArrValue[1].ToString() + " value3=" + dbArrValue[2].ToString()); } else MessageBox.Show("Test is Fail!!"); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.15 setToolOffsetData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ setToolOffsetData ” API 함수는 Tool offset data를 NC에 설정하는 API 함수 입니다.

- API 함수 원형 setToolOffsetData API함수의 원형은 다음과 같습니다.
C++

| int setToolOffsetData( __IN const char* channel, __IN const char* number, __IN const char* type, __IN int* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN const char* channel, __IN const char* number, __IN const char* type, __IN double* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN const char* channel, __IN const char* number, __IN const char* type, __IN char** data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN int* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN double* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN char** data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

파라미터 setToolOffsetData API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 계통 번호 |
| number | Tool Offset 번호 |
| type | Tool Offset 타입 번호 |
| data | NC에 설정할 Tool offset data |
| dataCnt | data의 총 개수 |
| result | 함수 실행 결과 관련 정보 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C#

| int setToolOffsetData( __IN string channel, __IN string number, __IN string type, __IN int[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN string channel, __IN string number, __IN string type, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN string channel, __IN string number, __IN string type, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN int[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setToolOffsetData( __IN int channel, __IN int number, __IN int type, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 setToolOffsetData API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 계통 번호 |
| number | Tool Offset 번호 |
| type | Tool Offset 타입 번호 |
| data | NC에 설정할 Tool offset data |
| result | 함수 실행 결과 관련 정보 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

type 파라미터에 입력 가능한 값은 다음과 같습니다.

| type | FANUC | MITSUBISHI | | |
| ---- | ---------------------- | ---------- | ---------------------- | ---------- |
| 밀링 | 선반 | 밀링 | 선반 | |
| 0 | | T | | T |
| 1 | Tool length/geometry | Geometry X | Tool length/geometry | Geometry X |
| 2 | Tool length/wear | Wear X | Tool length/wear | Wear X |
| 3 | Cutter radius/geometry | Geometry Y | Cutter radius/geometry | Geometry Y |
| 4 | Cutter radius/wear | Wear Y | Cutter radius/wear | Wear Y |
| 5 | | Geometry Z | | Geometry Z |
| 6 | | Wear Z | | Wear Z |
| 7 | | Geometry R | | Geometry R |
| 8 | | Wear R | | Wear R |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 SIEMENS에서는 해당 함수와 대응 되는 기능이 존재하지 않습니다. 해당 기능 사용시 오류 코드가 반환 됩니다.

- 예제
C++

| { int iCh; int iOffsetNum; int iMachineTypeInfo; int iTypeInfo; double dbSetValue; int iRst = 0xFF; iCh = 1; iOffsetNum = 1; dbSetValue = 1.5; iMachineTypeInfo = 1; iTypeInfo = 1; ITEM_HANDLE resultitem = new Item; iRst = m_api->setToolOffsetData(iCh, iOffsetNum, iTypeInfo, &dbSetValue, resultitem); if (iRst == 0x00) MessageBox.Show("Test is Success!!"); else MessageBox.Show("Test is Fail!!"); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { int iCh; int iOffsetNum; int iMachineTypeInfo; int iTypeInfo; double dbSetValue; int iRst = 0xFF; Item rstItem; iCh = 1; iOffsetNum = 1; dbSetValue = 1.5; iMachineTypeInfo = 1; iTypeInfo = 1; iRst = Api.setToolOffsetData(iCh, iOffsetNum, iTypeInfo, new double[] { dbSetValue }, out rstItem); if (iRst == 0x00) MessageBox.Show("Test is Success!!"); else MessageBox.Show("Test is Fail!!"); } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.16 getGModal
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명
“ getGModal ” API 함수는 해당 계통의 GModal 정보를 문자열 리스트의 형태로 한꺼번에 가져오는 API 함수 입니다.
- API 함수 원형 getGModal API함수의 원형은 다음과 같습니다.
C++

| int getGModal( __IN int channel, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getGModal( __IN int channel, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------- |

파라미터 getGModal API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 계통 번호 |
| result | 반환 데이터 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| ITEM_HANDLE result = new Item; int res = api->getGModal(1, result); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------- |

C#

| Item result = null; int res = Api.getGModal(1, out result); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.17 getExModal
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명
“ getExModal ” API 함수는 해당 계통의 GModal 외의 다른 모달 값을 가져오는 API 함수 입니다.
- API 함수 원형 getExModal API함수의 원형은 다음과 같습니다.
C++

| int getExModal( __IN int channel, __IN const char* modal, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getExModal( __IN int channel, __IN string modal, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------ |

파라미터 getExModal API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 계통 번호 |
| modal | Modal code |
| result | 반환 데이터 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

modal 파라미터에 입력 가능한 값은 다음과 같습니다.

| modal | FANUC | SIEMENS | MITSUBISHI | KCNC |
| ----- | -------------------------- | ------- | ---------- | ---- |
| - | O | | | |
| A | O | | | |
| B | O (2nd auxiliary function) | | O (B1과 동일) | |
| B1 | | | O | |
| B2 | | | O | |
| B3 | | | O | |
| B4 | | | O | |
| C | O | | | |
| D | O | O | | O |
| E | | O | | |
| F | O | | | |
| H | O [M] | O | | O |
| I | O | | | |
| J | O | | | |
| K | O | | | |
| L | O | | | |
| M | O | O | O (M1과 동일) | O |
| M1 | | | O | |
| M2 | O (2nd M code) | | O | |
| M3 | O (3rd M code) | | O | |
| M4 | | | O | |
| N | O | | | |
| O | O | | | |
| P | O [M] | | | |
| Q | O [M] | | | |
| R | O [M] | | | |
| S | O | O | O | |
| T | O | O | O | |
| U | O | | | |
| V | O | | | |
| W | O | | | |
| X | O | | | |
| Y | O | | | |
| Z | O | | | |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| ITEM_HANDLE result = new Item; int res = api->getExModal(1, 1, result, 1); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------- |

C#

| Item result = null; int res = Api.getExModal(1, "1", out result, 1); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.18 getGudData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ getGudData ” API 함수는 Gud Data를 읽어오는 기능을 제공하는 API 함수입니다. (SIEMENS Only)

- API 함수 원형 getGudData API함수의 원형은 다음과 같습니다.
C++

| int getGudData( __IN GUD_TYPE dataType, __IN int number, __IN int count, __IN const char* address, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getGudData( __IN GUD_TYPE dataType, __IN int number, __IN int count, __IN string address, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getGudData API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| GUD_TYPE | data type |
| number | Gud 옵셋 번호 ※ 0부터 시작입니다. |
| count | 반환 데이터 갯수 |
| address | Gud address ※ Siemens HMI화면의 값을 입력하되 "[0],[1],"[0,1]"등은 입력하지 않아야 합니다. ※ 예시 : _SC_NCK_ROU_R[0] → _SC_NCK_ROU_R |
| direct | 주기/비주기 통신 옵션 |
| result | Gud 호출 반환값 |
| machine | machine number : DEFAULT = 0 |
| channel | 계통 number : DEFAULT = 1 ※ Global GUD는 값을 0으로 설정해야 합니다. |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값 GUD_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------- | --- | ------------ |
| GUD_STRING | 0 | 문자열 값을 갖는 타입 |
| GUD_DOUBLE | 1 | 실수형 값을 갖는 타입 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 해당 함수는 SIEMENS에서만 사용 가능합니다.

- 예제
C++

| { Item result; int type = 0;//0 - string, 1 - double const char* straddress = "S_GC_CONT_S"; const char* doubleaddress = "_SC_CHUCK"; int res = -1; if (type == 0) res = api->getGudData(GUD_STRING, 1, 3, straddress, &result, 1, 1); else res = api->getGudData(GUD_DOUBLE, 1, 3, doubleaddress, &result, 1, 1); if (res != 0) { printf("[getGudData] res = %d", res); //index++; return; } const Value& a = result["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t if (a[i].IsString()) printf("[getUserVariable] value = %s / ", a[i].GetString()); //index++; else if (a[i].IsDouble()) printf("[getUserVariable] value = %f / ", a[i].GetDouble()); //index++; } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item item = null; string address = "S_GC_CONT_S"; string doubleaddress = "_SC_CHUCK"; int dtype = 1; int res = -1; if (dtype == 0) res = Api.getGudData(Api.GUD_TYPE.STRING, 1, 3, address, out item, 1, 1); else res = Api.getGudData(Api.GUD_TYPE.DOUBLE, 1, 3, doubleaddress, out item, 1, 1); string result_value = ""; if (iRst == 0x00 && resVal != null) { List<Item> tempData = (List<Item>)resVal.GetValue(); Item tmpItem = tempData[0]; iValue = tmpItem.GetArrayDouble("value"); if (iValue != null) { foreach (double val in iValue) { result_value += val.ToString() + ", "; } } } } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.2.19 setGudData
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.2 Data Access API 

- API 함수 설명 “ setGudData ” API 함수는  Gud Data를 갱신하는 기능을 제공하는 API 함수입니다. (SIEMENS Only)

- API 함수 원형 setGudData API함수의 원형은 다음과 같습니다.
- Siemens C++

| int setGudData( __IN GUD_TYPE dataType, __IN int number, __IN int count, __IN const char* address, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setGudData( __IN int number, __IN int count, __IN const char* address, __IN double* data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setGudData( __IN int number, __IN int count, __IN const char* address, __IN char** data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int setGudData( __IN GUD_TYPE dataType, __IN int number, __IN int count, __IN string address, __IN Item data, __OUT out Item result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setGudData( __IN int number, __IN int count, __IN string address, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setGudData( __IN int number, __IN int count, __IN string address, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 setGudData API 함수의 파라메터는 다음과 같습니다. - Siemens

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| GUD_TYPE | data type |
| number | Gud 옵셋 번호 ※ 0부터 시작입니다. |
| count | 입력 데이터 갯수 |
| address | Gud address ※ Siemens HMI화면의 값을 입력하되 "[0],[1],"[0,1]"등은 입력하지 않아야 합니다. ※ 예시 : _SC_NCK_ROU_R[0] → _SC_NCK_ROU_R |
| data | Gud 입력 데이터 |
| result | |
| machine | machine number : DEFAULT = 0 |
| channel | 계통 number : DEFAULT = 1 ※ Global GUD는 값을 0으로 설정해야 합니다. |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값
GUD_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| -------- | --- | ------------ |
| STRING | 0 | 문자열 값을 갖는 타입 |
| DOUBLE | 1 | 실수형 값을 갖는 타입 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
해당 함수는 SIEMENS에서만 사용 가능합니다.
- 예제
C++

| { const char* address = "S_GC_CONT_S"; const char* doubleaddress = "_SC_CHUCK"; const char* str = "{\"value\": [ \"sample12\", \"sample24\" ]}"; const char* dstr = "{\"value\": [ 123 ]}"; double dval[2] = { 456, 124 }; char** sdata = new char* [2]; sdata[0] = new char[10]; sdata[1] = new char[10]; strcpy(sdata[0], "sam"); strcpy(sdata[1], "sam1"); Item item; Item data, data1; data.Parse(str); data1.Parse(dstr); //type 정의 했을때 int type = 1;//0 - string, 1 - double, 2 - char**, 3 - double[] int res = -1; if (type == 0) res = api->setGudData(GUD_STRING, 1, 2, address, &data, &item, 1, 1); else if (type == 1) res = api->setGudData(GUD_DOUBLE, 1, 1, doubleaddress, &data1, &item, 1, 1); else if (type == 2) res = api->setGudData(1, 2, address, sdata, &item, 1, 1); else res = api->setGudData(1, 2, doubleaddress, dval, &item, 1, 1); if (res != 0) { printf("[setGudData] res = %d", res); //index++; return; } } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item item = null; string address = "S_GC_CONT_S"; string doubleaddress = "_SC_CHUCK"; int dtype = 1; //0-string, 1 - double, 2 -string[], 3 - double [] int res = -1; string data = "{\"value\": [ 500, 502 ]}"; ; string[] strdata = { "sample111", "sample222" }; double[] doubledata = { 600, 601 }; ItemTextParser parser = new ItemTextParser(); string itemstr = data; itemstr = itemstr.Replace("\t", ""); itemstr = itemstr.Replace("\r", ""); itemstr = itemstr.Replace("\n", ""); Item datas = null; datas = parser.Parse(itemstr); if (dtype == 0) res = Api.setGudData(Api.GUD_TYPE.STRING, 1, 2, address, datas, out item, 1, 1); else if (dtype == 1) res = Api.setGudData(Api.GUD_TYPE.DOUBLE, 1, 2, doubleaddress, datas, out item, 1, 1); else if (dtype == 2) res = Api.setGudData(1, 2, address, strdata, out item, 1); else res = Api.setGudData(1, 2, doubleaddress, doubledata, out item, 1); if (res != 0) { ..... } } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |
| |

---

#### 7.2.3 File Access API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

CNC File Access를 위한 API 설명 입니다. 

---

##### 7.2.3.1 getAttributeExists
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeExists ” API 함수는 NC의 파일 혹은 폴더가 존재하는지 확인합니다.

- API 함수 원형 getAttributeExists API함수의 원형은 다음과 같습니다.
C++

| int getAttributeExists( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeExists( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributeExists API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일 혹은 폴더의 전체 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로의 파일 혹은 폴더의 존재 여부 값 (true : 파일 혹은 폴더가 존재, false : 파일 또는 폴더가 존재하지 않음) |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 반환값이 실패여도 해당 폴더나 파일이 존재하지 않는다는 의미가 아닙니다. 존재 여부는 result 값을 확인해야 합니다. FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = api->getAttributeExists(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeExists(path, out outData); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.2 getAttributeType
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeType ” API 함수는 입력경로가 파일인지 폴더인지를 확인합니다.

- API 함수 원형 getAttributeType API함수의 원형은 다음과 같습니다.
C++

| int getAttributeType( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeType( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributeType API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일 혹은 폴더의 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로의 파일 혹은 폴더 여부 값 (0 : 폴더, 1 : 파일, 2 : 동일한 경로와 이름을 가진 폴더와 파일이 둘다 있는 경우) |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. path 파라미터의 입력 경로의 끝에 "/"가 있으면 폴더만 확인하므로 결과는 실패 또는 0(폴더) 뿐입니다. path 파라미터의 입력 경로의 끝에 "/"가 없으면 파일과 폴더를 모두 확인하므로 결과는 실패 또는 0(폴더), 1(파일), 2(둘다 있음) 입니다.

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = api->getAttributeType(path, outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeType(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.3 getAttributeIsNc
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeIsNc ” API 함수는 파일 혹은 폴더의 NC 내 위치 여부를 확인합니다.
- API 함수 원형 getAttributeIsNc API함수의 원형은 다음과 같습니다.
C++

| int getAttributeIsNc( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeIsNc( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getAttributeIsNc API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| path | 확인할 파일 혹은 폴더의 경로 |
| result | 입력 경로의 NC 내 위치 여부 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 SIEMENS에서만 사용가능 합니다.

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = api->getAttributeIsNc(path, outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeIsNc(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.4 getAttributeLogicalPath
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeLogicalPath ” API 함수는 객채의 논리적 경로를 가져옵니다.

- API 함수 원형 getAttributeLogicalPath API함수의 원형은 다음과 같습니다.
C++

| int getAttributeLogicalPath( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeLogicalPath( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------ |

파라메터 getAttributeLogicalPath API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| path | 확인할 파일 혹은 폴더의 경로 |
| result | 입력 경로 객채의 논리적 경로 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 SIEMENS에서만 사용가능 합니다.

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = api->getAttributeLogicalPath(path, outData); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeLogicalPath(path, out outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.5 getAttributeName
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeName ” API 함수는 파일 혹은 폴더의 이름 정보를 가져옵니다.

- API 함수 원형 getAttributeName API함수의 원형은 다음과 같습니다.
C++

| int getAttributeName( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeName( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributeName API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일 혹은 폴더의 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로의 파일 혹은 폴더의 이름 정보 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = m_api->getAttributeName(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeName(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.6 getAttributePath
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributePath ” API 함수는 파일 객체의 실제 경로를 가져옵니다.

- API 함수 원형 getAttributePath API함수의 원형은 다음과 같습니다.
C++

| int getAttributePath( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributePath( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributePath API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일의 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로 파일의 실제 경로 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = m_api->getAttributePath(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributePath(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.7 getAttributeSize
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeSize ” API 함수는 파일 객체의 파일크기를 가져옵니다. 알수 없는 경우에는 -1가 출력됩니다. (단위 : byte)

- API 함수 원형 getAttributeSize API함수의 원형은 다음과 같습니다.
C++

| int getAttributeSize( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeSize( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributeSize API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일의 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로 파일의 크기 값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = m_api->getAttributeSize(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeSize(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.8 getAttributeEditedTime
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getAttributeEditedTime ” API 함수는 파일 객체의 마지막으로 수정된 시간을 가져옵니다. (형식 : yyyy-MM-ddTHH:mm:ss)

- API 함수 원형 getAttributeEditedTime API함수의 원형은 다음과 같습니다.
C++

| int getAttributeEditedTime( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getAttributeEditedTime( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getAttributeEditedTime API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 파일의 경로 - 입력 경로의 끝에 "/"가 있으면 해당 경로와 이름의 폴더만 확인합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 해당 경로와 이름의 파일과 폴더를 확인합니다. (예: "//NC/tmp" tmp라는 이름의 폴더와 파일) |
| result | 입력 경로 파일의 마지막 수정된 시간 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = m_api->getAttributeEditedTime(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.getAttributeEditedTime(path, out outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.9 getFileList
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ getFileList ” API 함수는 폴더의 내용물의 이름을 나열합니다.

- API 함수 원형 getFileList API함수의 원형은 다음과 같습니다.
C++

| int getFileList( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getFileList( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------ |

파라미터 getFileList API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 폴더의 경로 - 폴더만 입력 가능합니다. (예: "//NC/dir/" 또는 "//NC/dir") - 각 NC Vendor별 최상위 폴더는 "5.2.1.1 ncMemory"의 rootPath 데이터 모델로 알 수 있습니다. |
| result | 입력 경로 폴더의 내용물 (파일 또는 폴더의 이름입니다. 폴더일 경우 끝에 "/"가 붙어 있습니다.) |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 Item class로 제공 받는 결과값 ( result ) 이 NULL 인 경우 폴더에 파일이 없다는 의미입니다.

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR"; int res = m_api->getFileList(path, outData); if (res != 0 || item == NULL) { if ( item == NULL ) printf("[getFileList] 폴더에 파일이 없습니다."); else printf("[getFileList] res = %d", res); //index++; return; } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR"; int res = Api.getFileList(path, out outData); if (res != 0 || item == null) { if ( item == null ) printf("[getFileList] 폴더에 파일이 없습니다."); else printf("[getFileList] res = %d", res); //index++; return; } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.10 getFileListEx
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “ getFileListEx ” API 함수는 지정한 폴더 내의 폴더와 파일 속성들을 JSON형태의 리스트로 반환하는 기능입니다.

- API 함수 원형 getFileListEx API함수의 원형은 다음과 같습니다.
C++

| int getFileListEx( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

C#

| int getFileListEx( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------- |

파라미터 getFileListEx API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| path | 확인할 폴더의 경로 - 폴더만 입력 가능합니다. (예: "//NC/dir/" 또는 "//NC/dir") - 각 NC Vendor별 최상위 폴더는 "5.2.1.1 ncMemory"의 rootPath 데이터 모델로 알 수 있습니다. |
| result | 입력 경로 폴더의 내용물 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
NC Vendor에서 제공해주는 순서대로 결과가 반환됩니다. Item class로 제공 받는 결과값 ( result ) 이 NULL 인 경우 폴더에 파일이 없다는 의미입니다. 결과 데이터의 구조는 아래와 같습니다.

| 속성 | 데이터 타입 | 설명 |
| ----- | ------ | -------------------------------------------------------------------------------------------- |
| name | string | 파일 또는 폴더의 이름입니다. 폴더일 경우 끝에 "/"가 붙어 있습니다. |
| isDir | bool | 폴더인 경우 true, 파일인 경우 false입니다. |
| size | double | 폴더나 파일의 크기입니다. 알수 없는 경우에는 -1가 출력됩니다. (단위 : byte) |
| time | string | 폴더나 파일이 마지막으로 수정된 일시입니다. (형식 : yyyy-MM-ddTHH:mm:ss) 알수 없는 경우에는 "0000-00-00T00:00:00"가 출력됩니다. |

- 예제
C++

| { Item item; const char* path = "//CNC_MEM/USER/PATH1/"; int res = api->getFileListEx(path, &item, 1, 10000); if (res != 0 || item == NULL) { if ( item == NULL ) printf("[getFileListEx] 폴더에 파일이 없습니다."); else printf("[getFileListEx] res = %d", res); //index++; return; } const Value& array = item["value"]; if (array.IsArray() == false) return; int mcount = 0; Api::Value::ConstMemberIterator itr; for (int i = 0; i < array.Size(); i++) { itr = array[i].FindMember("name"); if (itr != array[i].MemberEnd()) { if (itr->value.IsString()) printf("[name] value = %s\n", itr->value.GetString()); } itr = array[i].FindMember("isDir"); if (itr != array[i].MemberEnd()) { if (itr->value.IsBool()) printf("[isDir] value = %d\n", itr->value.GetBool()); } itr = array[i].FindMember("size"); if (itr != array[i].MemberEnd()) { if (itr->value.IsNumber() && itr->value.IsInt()) printf("[size] value = %d\n", itr->value.GetInt()); else if (itr->value.IsNumber() && itr->value.IsDouble()) printf("[size] value = %0.3f\n", itr->value.GetDouble()); else printf("[size] value error\n"); } itr = array[i].FindMember("time"); if (itr != array[i].MemberEnd()) { if (itr->value.IsString()) printf("[time] value = %s\n", itr->value.GetString()); } } } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item item = null; string path = "//CNC_MEM/USER/PATH1/"; int res = Api.getFileListEx(path, out item); if (res != 0x00 || item == null) { if ( item == null ) printf("[getFileListEx] 폴더에 파일이 없습니다."); else printf("[getFileListEx] res = %d", res); //index++; return; } else { List<Item> tempData = (List<Item>)item.GetValue(); Item tmpItem = tempData[0]; ItemArray itemArray = (ItemArray)tmpItem; foreach (Item item1 in itemArray) { string name = (string)item1.find("name").GetValue(); Item obj = (Item)item1.find("isDir"); bool isDir = false; if (obj != null) { isDir = Convert.ToBoolean(obj.GetValue()); } obj = (Item)item1.find("size"); double msize = 0.0; if (obj != null) { msize = Convert.ToDouble(obj.GetValue()); } string time = (string)item1.find("time").GetValue(); } } } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.11 CreateCNCFile
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “ CreateCNCFile ” API 함수는 NC내에 새로운 파일을 생성합니다.

- API 함수 원형 CreateCNCFile API함수의 원형은 다음과 같습니다.
C++ 새로운 파일의 전체 경로(경로 + 새로운 파일명)를 입력하는  함수 (예: path : "//NC/tmp/newfile" → 함수 실행 : "//NC/tmp/newfile" 파일 생성)

| int CreateCNCFile( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

새로운 파일의 경로와 새로운 파일명을 입력하는  함수 (예: path : "//NC/tmp/" & name : "newfile" → 함수 실행 : "//NC/tmp/newfile" 파일 생성)

| int CreateCNCFile( __IN const char* path, __IN const char* name, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- |

C# 새로운 파일의 전체 경로(경로 + 새로운 파일명)를 입력하는  함수 (예: path : "//NC/tmp/newfile" → 함수 실행 : "//NC/tmp/newfile" 파일 생성)

| int CreateCNCFile( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------- |

새로운 파일의 경로와 새로운 파일명을 입력하는  함수 (예: path : "//NC/tmp/" & name : "newfile" → 함수 실행 : "//NC/tmp/newfile" 파일 생성)

| int CreateCNCFile( __IN string path, __IN string name, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CreateCNCFile API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 생성할 파일의 전체 경로 (name 파라미터를 사용하지 않는 경우) - (예: "//NC/tmp/newfile") 또는 경로 (name 파라미터와 함께 사용하는 경우) - 폴더 경로로 인식 합니다. (예: "//NC/tmp/" 또는 "//NC/tmp") |
| name | 생성할 파일명 |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST2.MPF"; int res = api->CreateCNCFile(path, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/"; const char* name = "TEST2.MPF"; int res = api->CreateCNCFile(path, name, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST2.MPF"; int res = Api.CreateCNCFile(path, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| Item outData = null; string path = "//NC/MPF.DIR/"; string name = "TEST2.MPF"; int res = Api.CreateCNCFile(path, name, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.3.12 CreateCNCFolder
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “ CreateCNCFolder ” API 함수는 NC내에 새로운 폴더를 생성합니다.

- API 함수 원형 CreateCNCFolder API함수의 원형은 다음과 같습니다.
C++ 새로운 폴더의 전체 경로(경로 + 새로운 폴더명)를 입력하는  함수 (예: path : "//NC/tmp/newdir" → 함수 실행 : "//NC/tmp/newdir/" 폴더 생성)

| int CreateCNCFolder( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------- |

새로운 폴더의 경로와 새로운 폴더명을 입력하는  함수 (예: path : "//NC/tmp/" & name : "newdir" → 함수 실행 : "//NC/tmp/newdir/" 폴더 생성)

| int CreateCNCFolder( __IN const char* path, __IN const char* name, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C# 새로운 폴더의 전체 경로(경로 + 새로운 폴더명)를 입력하는  함수 (예: path : "//NC/tmp/newdir" → 함수 실행 : "//NC/tmp/newdir/" 폴더 생성)

| int CreateCNCFolder( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------- |

새로운 폴더의 경로와 새로운 폴더명을 입력하는  함수 (예: path : "//NC/tmp/" & name : "newdir" → 함수 실행 : "//NC/tmp/newdir/" 폴더 생성)

| int CreateCNCFolder( __IN string path, __IN string name, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CreateCNCFolder API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 생성할 폴더의 전체 경로 (name 파라미터를 사용하지 않는 경우) - 입력 경로 끝에 "/"가 없어야 합니다. (예: "//NC/tmp/newdir") 또는 경로 (name 파라미터와 함께 사용하는 경우) - 폴더 경로로 인식 합니다. (예: "//NC/tmp/" 또는 "//NC/tmp") |
| name | 생성할 폴더명 - 입력값에 "/"가 없어야 합니다. |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TESTFOLDER.DIR"; int res = api->CreateCNCFolder(path, outData); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/"; const char* name = "TESTFOLDER.DIR"; int res = api->CreateCNCFolder(path, name, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TESTFOLDER.DIR"; int res = Api.CreateCNCFolder(path, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| Item outData = null; string path = "//NC/MPF.DIR/"; string name = "TESTFOLDER.DIR"; int res = Api.CreateCNCFolder(path, name, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.13 CNCFileRename
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileRename ” API 함수는 파일 혹은 폴더 명칭을 수정합니다.

- API 함수 원형 CNCFileRename API함수의 원형은 다음과 같습니다.
C++

| int CNCFileRename( __IN const char* path, __IN const char* name, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int CNCFileRename( __IN string path, __IN string name, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CNCFileRename API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 수정할 파일 혹은 폴더의 경로 - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 또는 폴더 경로로 인식합니다. (예: "//NC/tmp" tmp라는 이름의 폴더 또는 파일) |
| name | 수정하고자 하는 파일 혹은 폴더의 새로운 이름 (예: path : "//NC/tmp/" & name : "tmp2" → 함수 실행 : "//NC/tmp/"에서 "//NC/tmp2/"로 폴더 이름 변경) (예: path : "//NC/tmp" & name : "tmp2" → 함수 실행 : "//NC/tmp"에서 "//NC/tmp2"로 폴더 또는 파일 이름 변경) |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; const char* name = "//NC/MPF.DIR/TEST1_RENAME.MPF"; int res = m_api->CNCFileRename(path, name, outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; string name = "//NC/MPF.DIR/TEST1_RENAME.MPF"; int res = Api.CNCFileRename(path, name, out outData); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.14 CNCFileCopy
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileCopy ” API 함수는 파일을 복사합니다.

- API 함수 원형 CNCFileCopy API함수의 원형은 다음과 같습니다.
C++

| int CNCFileCopy( __IN const char* source, __IN const char* target, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int CNCFileCopy( __IN string source, __IN string target, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CNCFileCopy API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| source | 복사 대상 파일 경로 - 파일이어야 합니다. (예: "//NC/tmp/test.nc") |
| target | 파일 복사 목표 경로 - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 경로로 인식합니다. (예: "//NC/tmp" tmp라는 이름의 파일) - 폴더 경로를 입력한 경우에는 파일명은 원본 파일명으로 복사 됩니다. (예: source : "//NC/tmp/test.nc" & target : "//NC/tmp2/" → 함수 실행 : "//NC/tmp2/test.nc" 경로로 복사) - 파일 경로를 입력한 경우에는 입력한 파일명으로 복사 됩니다. (예: source : "//NC/tmp/test.nc" & target : "//NC/tmp2/main.nc" → 함수 실행 : "//NC/tmp2/main.nc" 경로로 복사) |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; const char* name = "//NC/SPF.DIR/TEST1.MPF"; int res = m_api->CNCFileCopy(path, name, outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; string name = "//NC/SPF.DIR/TEST1.MPF"; int res = Api.CNCFileCopy(path, name, out outData); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.15 CNCFileMove
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileMove ” API 함수는 파일을 이동시킵니다.

- API 함수 원형 CNCFileMove API함수의 원형은 다음과 같습니다.
C++

| int CNCFileMove( __IN const char* source, __IN const char target, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int CNCFileMove( __IN string source, __IN string target, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CNCFileMove API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| source | 이동 대상 파일 경로 - 파일이어야 합니다. (예: "//NC/tmp/test.nc") |
| target | 파일 이동 목표 경로 - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 경로로 인식합니다. (예: "//NC/tmp" tmp라는 이름의 파일) - 폴더 경로를 입력한 경우에는 파일명은 원본 파일명으로 이동 됩니다. (예: source : "//NC/tmp/test.nc" & target : "//NC/tmp2/" → 함수 실행 : "//NC/tmp2/test.nc" 경로로 이동) - 파일 경로를 입력한 경우에는 입력한 파일명으로 이동 됩니다. (예: source : "//NC/tmp/test.nc" & target : "//NC/tmp2/main.nc" → 함수 실행 : "//NC/tmp2/main.nc" 경로로 이동) |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; const char* name = "//NC/SPF.DIR/TEST1.MPF"; int res = m_api->CNCFileMove(path, name, outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; string name = "//NC/SPF.DIR/TEST1.MPF"; int res = Api.CNCFileMove(path, name, out outData); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.16 CNCFileDelete
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileDelete ” API 함수는 파일 혹은 폴더를 삭제합니다.

- API 함수 원형
C++ CNCFileDelete API함수의 원형은 다음과 같습니다.

| int CNCFileDelete( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

C#

| int CNCFileDelete( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CNCFileDelete API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| path | 삭제 대상 파일 혹은 폴더의 경로 - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 또는 폴더 경로로 인식합니다. (예: "//NC/tmp" tmp라는 이름의 폴더 또는 파일) |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 FANUC NC에서는 동일한 경로와 이름을 가진 파일과 폴더가 동시에 존재할 수 있습니다. 입력 경로의 끝에 "/"가 있으면 폴더로, 없으면 파일로 인식합니다. 입력 경로의 끝에 "/"가 없고 해당 경로와 이름을 가진 파일과 폴더가 동시에 존재한다면 파일에 대해 우선 동작하며 파일이 없다면 폴더에 대해 동작합니다. - FANUC NC에서 폴더가 삭제 대상일 경우, 해당 폴더가 비어 있어야 삭제 됩니다. - KCNC NC에서 폴더가 삭제 대상일 경우, 해당 폴더 안에 있는 파일들이 삭제되고 해당 폴더도 삭제됩니다. 하지만 해당 폴더 안에 있는 폴더는 삭제되지 않습니다. 따라서 해당 폴더안에 폴더가 있는 경우 해당 폴더도 삭제되지 않습니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/TEST1.MPF"; int res = m_api->CNCFileDelete(path, outData); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/TEST1.MPF"; int res = Api.CNCFileDelete(path, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.3.17 CNCFileDeleteAll
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “ CNCFileDeleteAll ” API 함수는 지정한 폴더 내에 있는 모든 폴더와 파일을 삭제합니다. 지정한 폴더 자체는 삭제하지 않습니다.

- API 함수 원형 CNCFileDeleteAll API함수의 원형은 다음과 같습니다.
C++

| int CNCFileDeleteAll( __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int CNCFileDeleteAll( __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------- |

파라미터 CNCFileDeleteAll API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| path | 삭제 대상 폴더의 경로 - 폴더만 입력 가능합니다. (예: "//NC/dir/" 또는 "//NC/dir") |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 - FANUC NC에서 지정한 폴더 내에 있는 폴더들은 삭제되지 않습니다. 파일만 삭제 됩니다. - KCNC NC에서 지정한 폴더 내에 있는 폴더들은, 또다른 하위 폴더를 포함하고 있는 경우에는 삭제되지 않습니다.
- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/SPF.DIR/TESTFOLDER.DIR"; int res = m_api->CNCFileDeleteAll(path, outData); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/SPF.DIR/TESTFOLDER.DIR"; int res = Api.CNCFileDeleteAll(path, out outData); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.18 CNCFileExecute
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileExecute ” API 함수는 제어기 NC default 경로에 있는 가공 프로그램을 실행 프로그램으로 설정합니다.

- API 함수 원형 CNCFileExecute API함수의 원형은 다음과 같습니다.
C++

| int CNCFileExecute( __IN int channel, __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int CNCFileExecute( __IN int channel, __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 CNCFileExecute API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 사용하려는 계통 번호 |
| path | 실행시킬 파일의 경로 |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* path = "//NC/MPF.DIR/SWIVEL.MPF"; int res = m_api->CNCFileExecute(1, path, outData); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string path = "//NC/MPF.DIR/SWIVEL.MPF"; int res = Api.CNCFileExecute(1, path, out outData); if (res) { ............. } else { ........... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.19 CNCFileExecuteExtern
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명 “ CNCFileExecuteExtern ” API 함수는 제어기 NC default 경로 이외의 경로에 있는 가공 프로그램을 실행 프로그램으로 설정합니다.

- API 함수 원형 CNCFileExecuteExtern API함수의 원형은 다음과 같습니다.
C++

| int CNCFileExecuteExtern( __IN int channel, __IN const char* path, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int CNCFileExecuteExtern( __IN int channel, __IN string path, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 CNCFileExecuteExtern API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| channel | 사용하려는 계통 번호 |
| path | 실행시킬 파일의 경로 |
| result | 성공여부 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항

- 예제
C++

| ITEM_HANDLE outData = new Item; const char* strExtFilePath = "C:/MTPF/ExternTest.mpf"; int iSelChannel = 1; int res = m_api->CNCFileExecuteExtern(iSelChannel, strExtFilePath, outData); if (res) { ............. } else { ........... } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| Item outData = null; string strExtFilePath = "C:/MTPF/ExternTest.mpf"; int iSelChannel = 1; int res = Api.CNCFileExecuteExtern(iSelChannel, strExtFilePath, out outData); if (res) { ............. } else { ........... } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.20 UploadFile
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “UploadFile” API 함수는 LOCAL에 있는 파일을 NC로 upload 합니다. (LOCAL → NC)

- API 함수 원형 UploadFile API함수의 원형은 다음과 같습니다.
C++

| int UploadFile( __IN const char* local_path, __IN const char* nc_path, __IN int machine = 0, __IN int channel = 1, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ |

C#

| int UploadFile( __IN string local_path, __IN string nc_path, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 UploadFile API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| local_path | upload 대상이 되는 LOCAL내의 파일 경로 - 파일이어야 합니다. (예: "C:/temp/test.nc") - LOCAL은 TORUS가 설치된 컴퓨터를 의미합니다. |
| nc_path | upload 대상 파일이 저장될 NC 경로 - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "//NC/tmp/" tmp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 경로로 인식합니다. (예: "//NC/tmp" tmp라는 이름의 파일) - 폴더 경로를 입력한 경우에는 파일명은 upload 대상 파일명으로 upload 됩니다. (예: local_path : "C:/temp/test.nc" & nc_path : "//NC/tmp/" → 함수 실행 : "//NC/tmp/test.nc" 파일 생성) - 파일 경로를 입력한 경우에는 입력한 파일명으로 download 됩니다. (예: local_path : "C:/temp/test.nc" & nc_path : "//NC/tmp/main.nc" → 함수 실행 : "//NC/tmp/main.nc" 파일 생성) ※ 일부 NC는 파일명 변경이 허용되지 않습니다. 따라서 upload 시 nc_path는 폴더 경로를 사용하는 것을 권장합니다. ※ FANUC의 경우에는 파일명과 상관없이 파일 내용의 O 번호에 따라 파일명이 정해집니다.  ※ FANUC의 경우에는 파일 내용이 '%'로 시작되어야 합니다.  |
| machine | machine number : DEFAULT = 0 |
| channel | 계통 번호 : DEFAULT = 1 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 60000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| const char* local_path = "C:\\NCData\\IMP.NC"; const char* nc_path = "//NC/MPF.DIR/"; int res = m_api->UploadFile(local_path, nc_path); if (res) { ............. } else { ........... } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| string local_path = "C:\\NCData\\IMP.NC"; string nc_path = "//NC/MPF.DIR/"; int res = Api.UploadFile(local_path, nc_path); if (res) { ............. } else { ........... } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.3.21 DownloadFile
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.3 File Access API 

- API 함수 설명
- “DownloadFile" API 함수는 NC에 있는 파일을 LOCAL로 download 합니다. (NC → LOCAL)

- API 함수 원형 DownloadFile API함수의 원형은 다음과 같습니다.
C++

| int DownloadFile( __IN const char* nc_path, __IN const char* local_path, __IN int machine = 0, __IN int channel = 1, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int DownloadFile( __IN string nc_path, __IN string local_path, __IN int machine = 0, __IN int channel = 1, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라미터 DownloadFile API 함수의 파라미터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| nc_path | download 대상이 되는 NC내의 파일 경로 - 파일이어야 합니다. (예: "//NC/tmp/test.nc") |
| local_path | download 대상 파일이 저장될 LOCAL 경로 - LOCAL은 TORUS가 설치된 컴퓨터를 의미합니다. - 입력 경로의 끝에 "/"가 있으면 폴더 경로로 인식합니다. (예: "C:/temp/" temp라는 이름의 폴더) - 입력 경로의 끝에 "/"가 없으면 파일 경로로 인식합니다. (예: "C:/temp" temp라는 이름의 파일) - 폴더 경로를 입력한 경우에는 파일명은 download 대상 파일명으로 download 됩니다. (예: nc_path : "//NC/tmp/test.nc" & local_path : "C:/temp/" → 함수 실행 : "C:/temp/test.nc" 파일 생성) - 파일 경로를 입력한 경우에는 입력한 파일명으로 download 됩니다. (예: nc_path : "//NC/tmp/test.nc" & local_path : "C:/temp/main.nc" → 함수 실행 : "C:/temp/main.nc" 파일 생성) ※ 일부 NC는 파일명 변경이 허용되지 않습니다. 따라서 download 시 local_path는 폴더 경로를 사용하는 것을 권장합니다. |
| machine | machine number : DEFAULT = 0 |
| channel | 계통 번호 : DEFAULT = 1 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 60000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| const char* nc_path = "//NC/MPF.DIR/IMP.NC"; const char* local_path = "C:\\NCData\\"; int res = m_api->DownloadFile(nc_path, local_path); if (res) { .............. } else { ............ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| string nc_path = "//NC/MPF.DIR/IMP.NC"; string local_path = "C:\\NCData\\"; int res = Api.DownloadFile(nc_path, local_path); if (res) { .............. } else { ............ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

#### 7.2.4 Application Control
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 Application에 명령 또는 데이터를 전달할 수 있는 API를 설명합니다. 

---

##### 7.2.4.1 controlApp
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ controlApp ” API 함수는 특정 Application에 명령을 전달하는 기능을 제공하는 API 함수입니다.

- API 함수 원형 controlApp API함수의 원형은 다음과 같습니다.
C++

| int controlApp( __IN int cmd, __IN const char* address, __IN ITEM_HANDLE item, __OUT ITEM_HANDLE result, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int controlApp( __IN int cmd, __IN string address, __IN Item item, __OUT out Item result, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 controlApp API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| cmd | CONTROLAPP_CMD 또는 USER_DEFINE_CMD |
| address | App이 제공하는 Data의 주소 |
| item | 전달하고자 하는 데이터의 Item 형식 |
| result | 성공 여부에 대한 결과값 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ------------------- | --- | -------------------------------- |
| CMD_UNKNOWN | 0 | |
| CMD_ON_CREATE | 1 | Application에 Create 명령을 전달 |
| CMD_ON_SHOW | 2 | Application에 Show 명령을 전달 |
| CMD_ON_HIDE | 3 | Application에 Hide 명령을 전달 |
| CMD_ON_DESTROY | 4 | Application에 Destroy 명령을 전달 |
| CMD_ON_RUN | 5 | Application에 Run 명령을 전달 |
| CMD_ON_PAUSE | 6 | Application에 Pause 명령을 전달 |
| CMD_ON_STOP | 7 | Application에 Stop 명령을 전달 |
| CMD_ON_SHOWMODAL | 8 | Application에 Modal 실행 명령을 전달 |
| CMD_ON_DELIVERYFILE | 9 | Application에 Deliveryfile 명령을 전달 |
| USER_DEFINE_DEFAULT | 100 | 사용자 정의 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| Api::Item data; Api::Item result; data.Parse("{\"layout\":\"full\"}"); // callback 을 보낼 App 지정, 해당 App에 register_callback이 등록 되어 있어야 함. string appname = "CommandTester"; string address = "data://" + appname; api->controlApp((int)CMD_ON_SHOW, address.c_str(), &data, &result); if (result != null) { ............ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

예제 ( USER_DEFINE_DEFAULT )

| Api::Item data; Api::Item result; data.Parse("{\"layout\":\"full\"}"); // callback 을 보낼 App 지정, 해당 App에 register_callback이 등록 되어 있어야 함. string appname = "CommandTester"; string address = "data://" + appname; api->controlApp((int)USER_DEFINE_DEFAULT, address.c_str(), &data, &result); if (result != null) { ............ } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| ItemTextParser parser = new ItemTextParser(); Item item = parser.Parse("{\"control\" : \"app\"}"); Item result = null; Api.controlApp((int)CONTROLAPP_CMD.ON_SHOW, "data://app sample", item, out result); if (result != null) { ............ } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

예제 ( USER_DEFINE_CMD )

| ItemTextParser parser = new ItemTextParser(); Item item = parser.Parse("{\"control\" : \"app\"}"); Item result = null; Api.controlApp((int)USER_DEFINE_CMD.DEFAULT, "data://app sample", item, out result); if (result != null) { ............ } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.4.2 broadcast
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ broadcast ” API 함수는 모든 Application에 명령을 전달하는 기능을 제공하는 API 함수입니다.

- API 함수 원형 broadcast API함수의 원형은 다음과 같습니다.
C++

| int broadcast( __IN int cmd, __IN ITEM_HANDLE item, ); |
| ------------------------------------------------------ |

C# ( UserDefine command 사용 함수 )

| int broadcast( __IN int cmd, __IN Item item, ); |
| ----------------------------------------------- |

- 파라메터 broadcast API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------------- |
| cmd | 발생시킬 broadcast 이벤트 종류 |
| item | broadcast 이벤트로 전달할 데이터 |

- 열거형 값 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------------------------- | --- | --------------------------------- |
| BROADCAST_ON_ALARM | 0 | Application에 Alarm이 발생했음을 전달 |
| BROADCAST_ON_APPDEFINE | 1 | Application에 Appdefine이 발생했음을 전달 |
| BROADCAST_ON_CHANGE_LANGUAGE | 2 | Application에 Language 가 변경되었음을 전달 |
| BROADCAST_ON_HIDE | 3 | Application에 Hide요청이 발생했음을 전달 |
| USER_DEFINE_DEFAULT | 100 | 사용자 정의 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 이 함수를 실행하면 모든 Application에 이벤트가 발생합니다. Application은 이벤트 핸들러를 등록해야 전달 받을 수 있습니다.
- 예제
C++

| api->regist_callback((int)CALLBACK_BROADCAST, OnBroadcastCallback); Item item; item.SetString("name", 4); int res = api->broadcast((int)BROADCAST_ON_ALARM, &item); if (res != 0) printf("error\n"); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

예제 ( USER_DEFINE_DEFAULT )

| api->regist_callback((int)CALLBACK_BROADCAST, OnBroadcastCallback); Item item; item.SetString("name", 4); int res = api->broadcast((int)USER_DEFINE_DEFAULT, &item); if (res != 0) printf("error\n"); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| ItemString itemStr = new ItemString(); itemStr.Name = "name"; itemStr.Value = "5"; Item item = (Item)itemStr; Api.broadcast((int)BROADCAST_CMD.ON_.ALARM, item); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |

예제 ( USER_DEFINE_CMD )

| ItemString itemStr = new ItemString(); itemStr.Name = "name"; itemStr.Value = "5"; Item item = (Item)itemStr; Api.broadcast((int)USER_DEFINE_CMD.DEFAULT, item); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.4.3 DeliveryFile
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ DeliveryFile ” API 함수는 Application에서 지정된 Application에 File Stream 객체를 전달하는 기능을 제공하는 API 함수입니다.

- API 함수 원형 DeliveryFile API함수의 원형은 다음과 같습니다.
C++

| int DeliveryFile( __IN const char* appname, __IN const char* path, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------ |

C#

| int DeliveryFile( __IN string appname, __IN string path, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------- |

파라메터 DeliveryFile API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| appname | File Stream 객체를 전달하고자 하는 Application Name |
| path | 전달하고자 하는 File 경로 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| const char* appname = "App Sample2"; const char* path = "C:\\Delivery File.txt"; m_api0>DeliveryFile(appname, path); |
| -------------------------------------------------------------------------------------------------------------------- |

C#

| string appname = "App Sample2"; string path = "C:\\Delivery File.txt"; Api.DeliveryFile(appname, path); |
| ------------------------------------------------------------------------------------------------------- |

---

##### 7.2.4.4 Terminate
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ Terminate ” API 함수는 플랫폼에 해당 Application이 종료 되었음을 통보하는 함수 입니다.

- API 함수 원형 Terminate API함수의 원형은 다음과 같습니다.
C++

| int Terminate( void ); |
| ---------------------- |

C#

| int Terminate( void ); |
| ---------------------- |

- 파라메터 Terminate API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | -------- |
| void | 파라미터 없음. |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 initialize시 등록한 Application의 사용 등록 해제를 의미하므로, Application 종료시 호출해주어야 합니다.

- 예제
C++

| { mapi->Terminate(); } |
| ---------------------- |

C#

| { Api.Terminate(); } |
| -------------------- |

---

##### 7.2.4.5 GuiLoaded
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ GuiLoaded ” API 함수는 해당 Application Load 되었음을 Platform에 알리는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 GuiLoaded API함수의 원형은 다음과 같습니다.
C++

| int GuiLoaded( void ); |
| ---------------------- |

C#

| int GuiLoaded( void ); |
| ---------------------- |

파라메터 GuiLoaded API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------- |
| void | 파라미터 없음 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항 Application이 생성시 initialize가 실행된 후 App 이 처음 화면에 표시될때 Platform 에 Load되었음을 통보해야 합니다.

- 예제
C++

| { api->GuiLoaded(); } |
| --------------------- |

C#

| void frmMain_Load(object sender, EventArgs e) { Api.GuiLoaded(); } |
| ------------------------------------------------------------------ |

---

##### 7.2.4.6 GuiClosed
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.4 Application Control 

- API 함수 설명 “ GuiClosed ” API 함수는 해당 Application이 정상종료 되었음을 Platform에 알려주는 기능을 제공하는 API 함수 입니다.

- API 함수 원형 GuiClosed API함수의 원형은 다음과 같습니다.
C++

| void GuiClosed( void ); |
| ----------------------- |

C#

| void GuiClosed( void ); |
| ----------------------- |

파라메터 GuiClosed API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------- |
| void | 파라미터 없음 |

- 반환 값 반환 값은 없습니다.

- 사용법 및 주의사항 Application이 종료 될때  App이 닫힌 후 Platform 에  App이 닫혔음을 통보합니다.
App 이 닫힌 후 Terminate 를 호출하여 initialize시 등록한 Application 의 사용 등록을 해제해야 합니다.
- 예제
C++

| { api->GuiClosed(); } |
| --------------------- |

C#

| protected override void OnFormClosed(FormClosedEventArgs e) { Api.GuiClosed(); Api.Terminate(); } |
| ------------------------------------------------------------------------------------------------- |

---

#### 7.2.5 PLC DataAccess API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

---

##### 7.2.5.1 getPlcSignal
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.5 PLC DataAccess API 

- API 함수 설명 “ getPlcSignal ” API 함수는 PLC Data를 읽어오는 기능을 제공하는 API 함수입니다.

- API 함수 원형 getPlcSignal API함수의 원형은 다음과 같습니다. C++
- FANUC

| int getPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __IN bool direct, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- SIEMENS

| int getPlcSignal( __IN const char* plcAddress, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN const char* plcAddress, __IN bool direct, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- |

- CSCAM & KCNC & Mitsubishi

| int getPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __IN bool direct, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C# - FANUC

| int getPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- SIEMENS

| int getPlcSignal( __IN string plcAddress, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN string plcAddress, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- |

- CSCAM & KCNC & Mitsubishi

| int getPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int getPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __IN bool direct, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 getPlcSignal API 함수의 파라메터는 다음과 같습니다. - FANUC

| Parameter 이름 | 설명 |
| -------------- | --------------------------------------------------------------------------- |
| FANUC_PLC_TYPE | data type |
| startAddress | start address |
| endAddress | end address |
| direct | 주기/비주기 통신 옵션 |
| result | plc 호출 반환값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- Siemens

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| plcAddress | plc address |
| direct | 주기/비주기 통신 옵션 |
| result | plc 호출 반환값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- CSCAM & KCNC & Mitsubishi

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| int | data type ( CSCAM_PLC_TYPE, KCNC_PLC_TYPE, MITSUBISHI_PLC_TYPE ) |
| count | 반환 데이터 갯수 |
| startAddress | start address |
| direct | 주기/비주기 통신 옵션 |
| result | plc 호출 반환값 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값
FANUC_PLC_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------- | --- | -------------------------------------------------------- |
| BYTE | 0 | Byte type |
| WORD | 1 | Word type |
| LONG | 2 | Long type |
| FLOATING32 | 4 | 32-bit floating-point type(30i-B Series/0i-F/PMi-A only) |
| FLOATING64 | 5 | 64-bit floating-point type(30i-B Series/0i-F/PMi-A only) |

CSCAM_PLC_TYPE & KCNC_PLC_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| -------- | --- | ----------------- |
| BIT | 0 | 0 또는 1까지 값을 갖는 타입 |
| LONG | 1 | 정수형 값을 갖는 타입 |
| DOUBLE | 2 | 실수형 값을 갖는 타입 |

MITSUBISHI_PLC_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| -------- | --- | ---------- |
| BIT | 1 | Bit type |
| BYTE | 8 | Byte type |
| WORD | 16 | Word type |
| DWORD | 32 | DWord type |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
PLC 데이터의 Address는 공용화 되어 있지 않으므로 각 제어기 별로 필요한 PLC 데이터 Address를 확인 후 작업해야 합니다. 각 제어기 별로 함수의 형태가 다르므로, 해당 제어기에 맞는 함수를 사용해야 합니다. ※ 이 함수는 추후 지원이 중단 될 수 있습니다.
- 예제
C++

| { Item item; int res = 0; int machine_ID = 1; int type = 0; // 0 = siemense , 1 = fanuc, 2 = cscam, 3 = kcnc if (type == 0) { res = api->getPlcSignal("IW0[4]", &item, machine_ID); if (res != 0) return; const Value& a = item["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t { int debug = 0; if (a[i].IsNumber()) { if (a[i].IsInt()) printf("[getPlcSignal] value = %d / ", a[i].GetInt()); else if (a[i].GetDouble()) printf("[getPlcSignal] value = %.3f / ", a[i].GetDouble()); //index++; } else if (a[i].IsString()) { printf("[getPlcSignal] value = %s / ", a[i].GetString()); //index++; } } } else if (type == 1) { res = api->getPlcSignal(FANUC_WORD, "D100", "D103", &item, machine_ID); if (res != 0) return; const Value& a = item["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getPlcSignal] value = %.3f / ", a[i].GetDouble()); //index++; } else if (type == 2) { res = api->getPlcSignal(CSCAM_DOUBLE, 4, "PM0525", &item, machine_ID); if (res != 0) return; const Value& a = item["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getPlcSignal] value = %.3f / ", a[i].GetDouble()); //index++; } else if (type == 3) { res = api->getPlcSignal(KCNC_DOUBLE, 4, "PM0525", &item, machine_ID); if (res != 0) return; const Value& a = item["value"]; assert(a.IsArray()); for (SizeType i = 0; i < a.Size(); i++) // Uses SizeType instead of size_t printf("[getPlcSignal] value = %.3f / ", a[i].GetDouble()); //index++; } } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { int iRst = 0xFF; int iTypeInfo; double[] iValue; Item resVal; string strReadAddr = ""; string strEndAddr = ""; int iCNCFlag = 1; //CNC Vendor 1 : fanuc, 2: siemens, 3 : cscam, 5 : kcnc int machine_ID = 1; switch (iCNCFlag) { // FANUC case 1: strReadAddr = "D100"; strEndAddr = "D103"; iRst = Api.getPlcSignal(Api.FANUC_PLC_TYPE.WORD, strReadAddr, strEndAddr, out resVal, machine_ID ); break; // SIEMENS case 2: strReadAddr = "IW0[4]"; iRst = Api.getPlcSignal(strReadAddr, out resVal, machine_ID); break; // CSCAM case 3: strReadAddr = "PM0525"; iRst = Api.getPlcSignal((int)Api.CSCAM_PLC_TYPE.DOUBLE, 4, strReadAddr, out resVal, machine_ID); //CSCAM break; // KCNC case 5: strReadAddr = "PM0525" iRst = Api.getPlcSignal((int)Api.KCNC_PLC_TYPE.DOUBLE, 4, strReadAddr, out resVal, machine_ID); //KCNC break; default: MessageBox.Show("Error: CNC Vendor info read error!!"); return; } string result_value = ""; if (iRst == 0x00 && resVal != null) { List<Item> tempData = (List<Item>)resVal.GetValue(); Item tmpItem = tempData[0]; iValue = tmpItem.GetArrayDouble("value");// tmpItem.GetValueInt("value"); if (iValue != null) { foreach (double val in iValue) { result_value += val.ToString() + ", "; } } } } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |

---

##### 7.2.5.2 setPlcSignal
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.5 PLC DataAccess API 

- API 함수 설명 “ setPlcSignal ” API 함수는 PLC Data를 갱신하는 기능을 제공하는 API 함수입니다.

- API 함수 원형 setPlcSignal API함수의 원형은 다음과 같습니다.
C++ - FANUC

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __IN int* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __IN double* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN const char* startAddress, __IN const char* endAddress, __IN char** data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- Simens

| int setPlcSignal( __IN const char* plcAddress, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN const char* plcAddress, __IN int* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN const char* plcAddress, __IN double* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN const char* plcAddress, __IN char** data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- CSCAM & KCNC

| int setPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __IN ITEM_HANDLE data, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __IN int* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __IN double* data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setPlcSignal( __IN int dataType, __IN int count, __IN const char* startAddress, __IN char** data, __IN int dataCnt, __OUT ITEM_HANDLE result, __IN int machine = 0, __IN int timeout = API_TIMEOUT_DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 setPlcSignal API 함수의 파라메터는 다음과 같습니다. - FANUC

| Parameter 이름 | 설명 |
| -------------- | --------------------------------------------------------------------------- |
| FANUC_PLC_TYPE | data type |
| startAddress | start address |
| endAddress | end address |
| data | plc 입력 데이터 |
| dataCnt | data의 총 개수 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

- Simens

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| plcAddress | plc address |
| data | plc 입력 데이터 |
| dataCnt | data의 총 개수 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

- CSCAM & KCNC

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| int | data type ( CSCAM_PLC_TYPE, KCNC_PLC_TYPE ) |
| count | 입력 데이터 갯수 |
| startAddress | start address |
| data | plc 입력 데이터 |
| dataCnt | data의 총 개수 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms |

C# - FANUC

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __IN Item data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __IN int[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN FANUC_PLC_TYPE dataType, __IN string startAddress, __IN string endAddress, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

- Simens

| int setPlcSignal( __IN string plcAddress, __IN Item data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN string plcAddress, __IN int[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setPlcSignal( __IN string plcAddress, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN string plcAddress, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- |

- CSCAM & KCNC

| int setPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __IN Item data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| int setPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __IN int[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __IN double[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| int setPlcSignal( __IN int dataType, __IN int count, __IN string startAddress, __IN string[] data, __OUT out Item result, __IN int machine = 0, __IN int timeout = (int)API_TIMEOUT.DEFAULT ); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

파라메터 setPlcSignal API 함수의 파라메터는 다음과 같습니다. - FANUC

| Parameter 이름 | 설명 |
| -------------- | --------------------------------------------------------------------------- |
| FANUC_PLC_TYPE | data type |
| startAddress | start address |
| endAddress | end address |
| data | plc 입력 데이터 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- Simens

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| plcAddress | plc address |
| data | plc 입력 데이터 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- CSCAM & KCNC

| Parameter 이름 | 설명 |
| ------------ | --------------------------------------------------------------------------- |
| int | data type ( CSCAM_PLC_TYPE, KCNC_PLC_TYPE ) |
| count | 입력 데이터 갯수 |
| startAddress | start address |
| data | plc 입력 데이터 |
| result | |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT.INFINITE = 0 , API_TIMEOUT.DEFAULT = 1000ms |

- 열거형 값 FANUC_PLC_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------- | --- | -------------------------------------------------------- |
| BYTE | 0 | Byte type |
| WORD | 1 | Word type |
| LONG | 2 | Long type |
| FLOATING32 | 4 | 32-bit floating-point type(30i-B Series/0i-F/PMi-A only) |
| FLOATING64 | 5 | 64-bit floating-point type(30i-B Series/0i-F/PMi-A only) |

CSCAM_PLC_TYPE & KCNC_PLC_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| -------- | --- | ----------------- |
| BIT | 0 | 0 또는 1까지 값을 갖는 타입 |
| LONG | 1 | 정수형 값을 갖는 타입 |
| DOUBLE | 2 | 실수형 값을 갖는 타입 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
PLC 데이터의 Address는 공용화 되어 있지 않으므로 각 제어기 별로 필요한 PLC 데이터 Address를 확인 후 작업해야 합니다. 각 제어기 별로 함수의 형태가 다르므로, 해당 제어기에 맞는 함수를 사용해야 합니다. ※ 이 함수는 추후 지원이 중단 될 수 있습니다.
- 예제
C++

| { Item item; int res = 0; int type = 0; // 0 = siemense , 1 = fanuc, 2 = CSCAM, 3 = KCNC int machine_ID = 1; if (type == 0) { char** data = new char* [4]; data[0] = new char[10]; data[1] = new char[10]; data[2] = new char[10]; data[3] = new char[10]; strcpy(data[0], "10"); strcpy(data[1], "15"); strcpy(data[2], "25"); strcpy(data[3], "35"); res = api->setPlcSignal("IW0[4]", data, 4, &item, machine_ID); if (res != 0) return; } else if (type == 1) { char** data = new char* [2]; data[0] = new char[10]; data[1] = new char[10]; strcpy(data[0], "10"); strcpy(data[1], "15"); res = api->setPlcSignal(FANUC_WORD, "D100", "D103", data, 2, &item, machine_ID); if (res != 0) return; } else if (type == 2) { double* data = new double[4]; data[0] = 123; data[1] = 456; data[2] = 789; data[3] = 978; res = api->setPlcSignal(CSCAM_DOUBLE, 4, "PM0525", data, 4, &item, machine_ID); if (res != 0) return; delete[] data; } else if (type == 3) { double* data = new double[4]; data[0] = 123; data[1] = 456; data[2] = 789; data[3] = 978; res = api->setPlcSignal(KCNC_DOUBLE, 4, "PM0525", data, 4, &item, machine_ID); if (res != 0) return; delete[] data; } } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { int iRst = 0xFF; int iTypeInfo; int iCNCFlag = 1; //CNC Vendor 1 : fanuc, 2: siemens, 3 : cscam, 5 : kcnc Item resVal; string strStartAddr = ""; string strEndAddr = ""; List<double> dbSetValueList = new List<double>(); string settext = "1.2,1.5,2.5"; string[] setTextarr = settext.Split(new char[] { ',', ' ' }); for (int i = 0; i < setTextarr.Length; i++) { double dval; if (Double.TryParse(setTextarr[i], out dval)) { dbSetValueList.Add(dval); } } double[] dbSetValue = dbSetValueList.ToArray(); switch (iCNCFlag) { // FANUC case 1: strStartAddr = "D100"; strEndAddr = "D103"; iRst = Api.setPlcSignal(Api.FANUC_PLC_TYPE.WORD, strStartAddr, strEndAddr, dbSetValue, out resVal, machine_ID); if (iRst != 0x00) MessageBox.Show("Error: FANUC setPlcSignal error!!"); break; // SIEMENS case 2: strStartAddr = "IW0[4]"; iRst = Api.setPlcSignal(strStartAddr, dbSetValue, out resVal, machine_ID); if (iRst != 0x00) MessageBox.Show("Error: SIEMENS setPlcSignal error!!"); break; // CSCAM case 3: strStartAddr = "PM0525"; iRst = Api.setPlcSignal( (int)Api.CSCAM_PLC_TYPE.DOUBLE, 3, strStartAddr, dbSetValue, out resVal, machine_ID); //CSCAM if (iRst != 0x00) MessageBox.Show("Error: CSCAM setPlcSignal error!!"); break; // KCNC case 5: strStartAddr = "PM0525"; iRst = Api.setPlcSignal( (int)Api.KCNC_PLC_TYPE.DOUBLE, 3, strStartAddr, dbSetValue, out resVal, machine_ID); //KCNC if (iRst != 0x00) MessageBox.Show("Error: CSCAM setPlcSignal error!!"); break; default: MessageBox.Show("Error: CNC Vendor info read error!!"); return; } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

#### 7.2.6 Extra  API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

---

##### 7.2.6.1 getMachinesInfo
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.6 Extra API 

- API 함수 설명 “getMachinesInfo” API 함수는 플랫폼에 연결된 다중 장비의 속성을 확인 할수 있도록 정보를 제공해주는 함수 입니다.

- API 함수 원형
C++ getMachinesInfo API함수의 원형은 다음과 같습니다.

| int getMachinesInfo( __OUT ITEM_HANDLE result, ); |
| ------------------------------------------------- |

C#

| int getMachinesInfo( __OUT Item result, ); |
| ------------------------------------------ |

파라메터 getMachinesInfo API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----------------------------------------- |
| result | 실행 결과 관련 Data Machine 의 정보가 배열 형태로 저장됩니다. |

결과 Data 속성 값

| 속성 | 데이터 type |
| ---------- | -------- |
| name | string |
| id | double |
| venderCode | string |
| ip_address | string |
| toolSystem | double |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
플랫폼에 연결된 장비들의 속성 만을  제공해 주는 함수입니다. MachineList.xml 에 등록되어 있더라도 연결되지 않은 경우에는 속성 정보가 제공되지 않습니다.
- 예제
C++

| { Item item; api->getMachinesInfo(&item); if (res != 0 || item == NULL) { printf("[getFileListEx] res = %d", res); //index++; return; } const Value& array = item["value"]; if (array.IsArray() == false) return; int mcount = 0; Api::Value::ConstMemberIterator itr; for (int i = 0; i < array.Size(); i++) { itr = array[i].FindMember("name"); if (itr != array[i].MemberEnd()) { if (itr->value.IsString()) printf("[name] value = %s\n", itr->value.GetString()); } itr = array[i].FindMember("id"); if (itr != array[i].MemberEnd()) { if (itr->value.IsNumber() && itr->value.IsDouble()) printf("[size] value = %0.3f\n", itr->value.GetDouble()); else printf("[size] value error\n"); } itr = array[i].FindMember("venderCode"); if (itr != array[i].MemberEnd()) { if (itr->value.IsString()) printf("[time] value = %s\n", itr->value.GetString()); } } } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| { Item item = null; int res = Api.getMachinesInfo(out item); if (res == 0x00 && item != null) { List<Item> tempData = (List<Item>)item.GetValue(); Item tmpItem = tempData[0]; ItemArray itemArray = (ItemArray)tmpItem; foreach (Item item1 in itemArray) { string name = (string)item1.find("name").GetValue(); Item obj = (Item)item1.find("id"); double mid = 0; if (obj != null) { mid = Convert.ToDouble(obj.GetValue()); } string vendercode = (string)item1.find("venderCode").GetValue(); ...... } } } |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |

---

#### 7.2.7 Log API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

---

##### 7.2.7.1 sendLog
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.7 Log API 

- API 함수 설명 “ sendLog ” API 함수는 Platform에 Log를 추가하는 API 함수 입니다.

- API 함수 원형 sendLog API함수의 원형은 다음과 같습니다.
C++

| int sendLog( __IN const char* msg, __OUT ITEM_HANDLE result, ); |
| --------------------------------------------------------------- |

C#

| int sendLog( __IN string msg, __OUT out Item result, ); |
| ------------------------------------------------------- |

파라메터 sendLog API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | -------------------- |
| msg | 추가하고자 하는 Log message |
| result | 추가 성공 여부 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
Log는 Platform 실행 경로의 Log\logManager.log 파일에 추가되며,  Text 편집기로 열어서 확인할 수 있습니다. mgrLog.exe 가 구동된 상태에서만 해당 함수가 동작합니다.
- 예제
C++

| { ITEM_HANDLE result = new Item; m_api->sendLog("To Left App Sample 2", result); } |
| ---------------------------------------------------------------------------------- |

C#

| Item result = null; Api.sendLog("To Left App Sample 2", out result); |
| -------------------------------------------------------------------- |

---

##### 7.2.7.2 sendLogEx
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.7 Log API 

- API 함수 설명 “ sendLogEx ” API 함수는 Platform에 Log를 추가하는 API 함수 입니다.

- API 함수 원형
sendLogEx API함수의 원형은 다음과 같습니다. C++

| int sendLogEx( __IN const char* msg, __OUT ITEM_HANDLE result, __IN int loglevel ); |
| ----------------------------------------------------------------------------------- |

C#

| int sendLogEx( __IN string msg, __OUT out Item result, __IN int loglevel = (int)LOGLEVEL.NORMAL ); |
| -------------------------------------------------------------------------------------------------- |

파라메터 sendLogEx API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | -------------------- |
| msg | 추가하고자 하는 Log message |
| result | 추가 성공 여부 |
| loglevel | Log의 레벨 지정 |

- 열거형 값 LOGLEVEL 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| -------- | --- | --- |
| NORMAL | 0 | |
| WARN | 1 | |
| ERR | 2 | |
| FATAL | 3 | |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
sendLog의 Log레벨은 default값을  NORMAL로 설정되지만 해당 함수의 경우 추가하고자 하는  Log에 다른 레벨을 지정할 수 있습니다. Log는 Platform 실행 경로의 Log\logManager.log 파일에 추가되며,  Text 편집기로 열어서 확인할 수 있으며, 제공된 Xtrace.exe 에서도 확인 가능합니다. mgrLog.exe 가 구동된 상태에서만 해당 함수가 동작합니다.
- 예제
C++

| ITEM_HANDLE result = new Item; m_api->sendLogEx("To Left App Sample 2", result, LOGLEVEL.WARN); |
| ----------------------------------------------------------------------------------------------- |

C#

| { Item result = null; Api.sendLogEx("To Left App Sample 2", out result, LOGLEVEL.WARN); } |
| ----------------------------------------------------------------------------------------- |

---

#### 7.2.8 Event Handler
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 Event Handler에 대해 설명 합니다 . 

---

##### 7.2.8.1 regist_callback
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.8 Event Handler 

- API 함수 설명 “ regist_callback ” API 함수는 callback 함수를 등록하는 API 함수 입니다.

- API 함수 원형 regist_callback API함수의 원형은 다음과 같습니다.
C++

| int regist_callback( __IN int callbackid, __IN callback_function func ); |
| ------------------------------------------------------------------------ |

파라메터 regist_callback API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----------------------------------------------------------------------------------------------------------- |
| callbackid | CALLBACK_TYPE |
| func | callback 함수 입니다. 원형 typedef int (*callback_function)(int evt, int cmd, const char* command, char** result); |

C#

| int regist_callback( __IN int callbackid, __IN CallbackString func, ); |
| ---------------------------------------------------------------------- |

파라메터 regist_callback API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----------------------------------------------------------------------------------------------------------- |
| callbackid | CALLBACK_TYPE |
| func | callback 함수 입니다. 원형 delegate int (*CallbackString)(EVENT_CODE evt, int cmd, Item command, ref Item result); |

- 열거형 값 CALLBACK_TYPE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ---------------------------------- | --- | ----------------------------- |
| CALLBACK_UNKNOWN | 0 | 알수 없는 타입 |
| CALLBACK_ON_GETDATA | 1 | Get Data Event |
| CALLBACK_ON_UPDATEDATA | 2 | Update Data Event |
| CALLBACK_ON_INSERTDATA | 3 | Insert Data Event |
| CALLBACK_ON_DELETEDATA | 4 | Delete Data Event |
| CALLBACK_ON_CONTROLAPP | 5 | Control App Event |
| CALLBACK_ON_BROADCAST | 6 | Broadcast Event |
| CALLBACK_ON_ALARM | 7 | Alarm Event |
| CALLBACK_ON_CREATE | 8 | Create Event |
| CALLBACK_ON_SHOW | 9 | Show Event |
| CALLBACK_ON_HIDE | 10 | Hide Event |
| CALLBACK_ON_DESTROY | 11 | Destroy Event |
| CALLBACK_ON_RUN | 12 | Run Event |
| CALLBACK_ON_PAUSE | 13 | Pause Event |
| CALLBACK_ON_STOP | 14 | Stop Event |
| CALLBACK_ON_CHANGE_LAYOUT | 15 | Change Layout Event |
| CALLBACK_ON_GETDATAASYNC | 17 | Get Data Async Event |
| CALLBACK_ON_GETDATAASYNCRESULT | 18 | Get Data Async Result Event |
| CALLBACK_ON_SUBSCRIBEDATA | 19 | Subscribe Data Event |
| CALLBACK_ON_RESGIST_SUBSCRIBEDATA | 20 | Regist Subscribe Data Event |
| CALLBACK_ON_UNREGIST_SUBSCRIBEDATA | 21 | UnRegist Subscribe Data Event |
| CALLBACK_ON_CLEAR_SUBSCRIBEDATA | 22 | Clear Subscribe Data Event |
| CALLBACK_ON_OBSERVER | 23 | Observer Event(현재 사용하지 않음) |
| CALLBACK_ON_DELIVERYFILE | 24 | 파일 전송 Event |
| CALLBACK_ON_TIMESERIESDATA | 27 | TimeSeries Data Event |
| CALLBACK_MAX | 28 | Event 개수 |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)

- 사용법 및 주의사항
- 예제
C++

| int onCreate(int evt, int cmd, const char* command, char** result) { char msg[1024] = { 0, }; sprintf_s(msg, "%s", command); printf_s("onShow command = %s\n", msg); return 0; } int main() { ..... CApi* api = CApi::Get(guid, "ConsoleControlApp"); int resulta = api->initialize(); if (resulta != 0) exit(0); api->GuiLoaded(); api->regist_callback((int)CALLBACK_TYPE::CALLBACK_ON_CREATE, onCreate); ... } |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

C#

| int OnCreate(EVENT_CODE evt, int cmd, Item command, ref Item result) { string msg = ""; msg = command.ToString() return 0; } int main() { Api.regist_callback((int)CALLBACK_TYPE.ON_CREATE, OnCreate); } |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.8.2 ApiEvent (C#)
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.8 Event Handler 

- 설명
ApiEvent는 일반적인 이벤트 핸들러를 구현하기위한 delicate 입니다.
- 원형 delegate void ApiEvent ( ApiEventArgs e);
- Event Handler
event ApiEvent OnEvent_GetData;                              //NC GetData 관련 Event Handler event ApiEvent OnEvent_UpdateData;                         //NC UpdateData 관련 EventHandler event ApiEvent OnEvent_InsertData;                           //NC InsertData 관련 EventHandler event ApiEvent OnEvent_DeleteData;                          //NC DeleteData 관련 EventHandler event ApiEvent OnEvent_Broadcast;                            //Application Broadcast 명령 관련 EventHandler event ApiEvent OnEvent_ChangeLayout;                      //Application Layout 변경 관련 EventHandler event ApiEvent OnEvent_ControlApp;                          //Application ControlApp 명령 관련 EventHandler event ApiEvent OnEvent_Show;                                  //Application Show 관련 EventHandler event ApiEvent OnEvent_Create;                                 //Application 생성 관련 EventHandler event ApiEvent OnEvent_Run;                                    //Application 실행 관련 EventHandler event ApiEvent OnEvent_Stop;                                   //Application 정지 관련 EventHandler event ApiEvent OnEvent_Pause;                                  //Application 일시정지 관련 EventHandler event ApiEvent OnEvent_Destroy;                                //Application 종료 관련 EventHandler event ApiEvent OnEvent_Hide;                                    //Application Hide 관련 EventHandler event ApiEvent OnEvent_GetDataAsync;                         //NC GetDataAsync 관련 EventHandler event ApiEvent OnEvent_GetDataAsyncResult;                  //NC GetDataAsyncResult 관련 EventHandler event ApiEvent OnEvent_SubscribeData;                         //NC SubscribeData 관련 EventHandler event ApiEvent OnEvent_RegistSubscribeData;                 //NC RegistSubscribeData 관련 EventHandler event ApiEvent OnEvent_UnregistSubscribeData;              //NC UnregistSubscribeData 관련 EventHandler event ApiEvent OnEvent_ClearSubscribeData;                   //NC ClearSubscribeData 관련 EventHandler event ApiEvent OnEvent_DeliveryFile;                            //Application 간 DeliveryFile 관련 EventHandler event ApiEvent OnEvent_TimeSeriesData;                        //NC TimeseriesData  관련 Event Handler
- 예제

| Api.OnEvent_GetData += Api_OnEvent_GetData; void Api_OnEvent_GetData(ApiEventArgs e) { MessageBox.Show(e.item.ToString()); } |
| ---------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.8.3 ApiEventArgs (C#)
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.8 Event Handler 

- 설명 Event 가 발생할때 전달되는 Argument에 대해 설명합니다.

- 생성자

| ApiEventArgs( EVENT_CODE eventcode, int command, string address, Item item, Item resultdata, ); |
| ----------------------------------------------------------------------------------------------- |

- 파라메터 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----------------------- |
| eventcode | EVENT_CODE |
| command | Event 발생 전달 command. |
| address | Event 발생 전달 address |
| item | Event 발생 전달 Item |
| resultdata | Event 발생 전달 Result Data |

- 열거형 값 EVENT_CODE 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ------------------ | --- | --------------------------------------------------- |
| UNKNOWN | 0 | |
| GETDATA | 1 | NC GetData 관련 Event가 발생할때 전달되는 Code |
| UPDATEDATA | 2 | NC UpdateData 관련 Event가 발생할때 전달되는 Code |
| INSERTDATA | 3 | NC InsertData 관련 Event가 발생할때 전달되는 Code |
| DELETEDATA | 4 | NC DeleteData 관련 Event가 발생할때 전달되는 Code |
| CONTROLAPP | 5 | Application ControlApp 명령 관련 Event가 발생할때 전달되는 Code |
| BROADCAST | 6 | Application Broadcast 명령 관련 Event가 발생할때 전달되는 Code |
| ALARM | 7 | Application Alarm 명령 관련 Event가 발생할때 전달되는 Code |
| GETDATAASYNC | 8 | NC GetDataAsync 관련 Event가 발생할때 전달되는 Code |
| GETDATAASYNCRESULT | 9 | NC GetDataAsyncResult 관련 Event가 발생할때 전달되는 Code |
| REGHOTLINK | 10 | NC RegistSubscribeData 관련 Event가 발생할때 전달되는 Code |
| UNREGHOTLINK | 11 | NC UnregistSubscribeData 관련 Event가 발생할때 전달되는 Code |
| HOTLINK | 12 | NC SubscribeData 관련 Event가 발생할때 전달되는 Code |
| CLEARHOTLINK | 13 | NC ClearSubscribeData 관련 Event가 발생할때 전달되는 Code |
| REGTIMESERIES | 14 | NC registTimeSeries 관련 Event가 발생할때 전달되는 Code |
| UNREGTIMESERIES | 15 | NC unregistTimeSeries 관련 Event가 발생할때 전달되는 Code |
| DELIVERYFILE | 16 | Application 간 DeliveryFile 관련 Event가 발생할때 전달되는 Code |
| TIMESERIESDATA | 19 | NC TimeSeriesData 관련 Event가 발생할때 전달되는 Code |

- 예제

| Api.OnEvent_GetData += Api_OnEvent_GetData; void Api_OnEvent_GetData(ApiEventArgs e) { MessageBox.Show(e.item.ToString()); } |
| ---------------------------------------------------------------------------------------------------------------------------- |

---

#### 7.2.9 XTrace API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 XTrace Class에 대해 설명 합니다 . “XTrace” 클래스는 IntelligentAPI에서 실시간 Trace 기능과 관련된 기능을 제공하는 클래스 입니다. 

---

##### 7.2.9.1 AddTraceMsg
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.9 XTrace API 

- API 함수 설명 “ AddTraceMsg ” API 함수는 “XTrace ” 클래스의 실시간 로그를 기록하는 함수입니다.

- API 함수 원형 AddTraceMsg API함수의 원형은 다음과 같습니다.
-
C++

| void AddTraceMsg( __IN int level, __IN const char* szMessages ); |
| ---------------------------------------------------------------- |

C#

| void AddTraceMsg( __IN int level, __IN string szMessage ); |
| ---------------------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | -------------------- |
| level | 실시간 로그 Level을 입력합니다. |
| message | 로그 메시지를 입력합니다. |

- 열거형 값 XTRACELEVEL 타입의 값은 다음과 같습니다.

| 열거형 값 이름 | 값 | 설명 |
| ----------------- | ----- | ----------------------------------------- |
| COMMAND_MGR | 0 | Platform Command Manager에서 전달하는 메시지 |
| COMMUNICATION_MGR | 1 | Platform Communication Manager에서 전달하는 메시지 |
| APPLICATION_MGR | 2 | Platform Application Manager 에서 전달하는 메시지 |
| DATABASE_MGR | 3 | Platform Database Maanger 에서 전달하는 메시지 |
| LOG_MGR | 4 | Platform Log Manager 에서 전달하는 메시지 |
| SECURITY_MGR | 5 | Platform Sequrity Manager 에서 전달하는 메시지 |
| LIBRARY | 10000 | Platform Library 에서 전달하는 메시지 |
| APPLICATION | 20000 | Application 에서 전달하는 메시지 |

- 반환 값 없음
- 사용법 및 주의사항 XtraceApp.exe를 통해 디버깅 내용을 실시간으로 확인할 수 있습니다.

- 예제
C++

| char* appName = "appTester"; m_api->AddTraceMsg((int)XTRACELEVEL::TRACE_LV_APPLICATION, appName); // |
| ---------------------------------------------------------------------------------------------------- |

C#

| string appName = "appTester"; Api.AddTraceMsg((int)XtraceLevel.APPLICATION., appName); // |
| ----------------------------------------------------------------------------------------- |

---

#### 7.2.10 TimeSeries API
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 XTrace Class에 대해 설명 합니다 . “XTrace” 클래스는 IntelligentAPI에서 실시간 Trace 기능과 관련된 기능을 제공하는 클래스 입니다. 

---

##### 7.2.10.1 startTimeSeries
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.10 TimeSeries API 

- API 함수 설명 “startTimeSeries” API 함수는 장비에서 제공하는 데이터를 시간 순서에 따라 수집을 시작하도록 하는 함수입니다.

- API 함수 원형 startTimeSeries API함수의 원형은 다음과 같습니다.
-
C++

| void startTimeSeries( __IN int buffer, __IN int machine, __IN int timeout = API_TIMEOUT_BUFFER ); |
| ------------------------------------------------------------------------------------------------- |

C#

| void startTimeSeries( __IN int buffer, __IN int machine, __IN int timeout = (int)API_TIMEOUT_BUFFER ); |
| ------------------------------------------------------------------------------------------------------ |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.
-

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------- |
| buffer | 수집을 시작할 buffer 번호 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms , API_TIMEOUT_BUFFER = 10000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)
- 사용법 및 주의사항 명령어 실행 후 NC로 부터 전달된 수집 TimeSeriesData는 C+++의 경우 사용자가 등록한  "CALLBACK_ON_TIMESERIESDATA " callback 함수 호출을  통해,
C# 은 " OnEvent_TimeSeriesData" 이벤트를 통해 값을 전달 받을수 있습니다. 또한, getData 함수를 이용하여 이전에 수집된 시계열 데이터를 전달 받을수도 있습니다. . ex) data://machine/buffer/stream/value?machine=i&buffer=j&stream=k
- 예제
C++

| int buffer_id = 1; int mac_id = 1; m_api->startTimeSeries(buffer_id, mac_id); |
| ----------------------------------------------------------------------------- |

C#

| int buffer_id = 1; int mac_id = 1; Api.startTimeSeries(buffer_id, mac_id); |
| -------------------------------------------------------------------------- |

---

##### 7.2.10.2 endTimeSeries
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.10 TimeSeries API 

- API 함수 설명 “endTimeSeries” API 함수는 장비에서의 시계열 데이터 수집을 종료하도록 하는 함수입니다.

- API 함수 원형 endTimeSeries API함수의 원형은 다음과 같습니다.
-
C++

| void endTimeSeries( __IN int buffer, __IN int machine, __IN int timeout = API_TIMEOUT_BUFFER ); |
| ----------------------------------------------------------------------------------------------- |

C#

| void endTimeSeries( __IN int buffer, __IN int machine, __IN int timeout = (int)API_TIMEOUT_BUFFER ); |
| ---------------------------------------------------------------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.
-

| Parameter 이름 | 설명 |
| ------------ | ---------------------------------------------------------------------------------------------------------- |
| buffer | 수집을 시작할 buffer 번호 |
| machine | machine number : DEFAULT = 0 |
| timeout | 데이터 송수신 Timeout 값 : API_TIMEOUT_INFINITE = 0 , API_TIMEOUT_DEFAULT = 1000ms , API_TIMEOUT_BUFFER = 10000ms |

- 반환 값 반환 값은 signed integer 값으로 API함수의 실행 결과를 나타내며 다음과 같은 의미가 있습니다. - 0x00: 성공 - 그 외 반환 값: 실패(Error code)
- 사용법 및 주의사항

- 예제
C++

| int buffer_id = 1; int mac_id = 1; m_api->endTimeSeries(buffer_id, mac_id); |
| --------------------------------------------------------------------------- |

C#

| int buffer_id = 1; int mac_id = 1; Api.endTimeSeries(buffer_id, mac_id); |
| ------------------------------------------------------------------------ |

---

#### 7.2.11 Item Class (C#)
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform 에서 지원하는 C#용 Item Class에 대해 설명 합니다 . “Item” 클래스는 IntelligentAPI에서 제공되는 데이터 구조 클래스 입니다. 

---

##### 7.2.11.1. Name
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “Name” API 함수는 Item Class 의 속성으로 객체의 이름을 정의 합니다.

- 예제

| //item json 형식 : {"MACHINE_INFO": {"value": [104.96],"address": "data://machine/channel/axis/machineposition","filter": "machine=1&channel=1&axis=1"}} Item item = null; Api.getData("data://machine/channel/axis/machineposition", "machine=1&channel=1&axis=1", out item, false); string itemstr = item.ToString(); item.Name = "MACHINE_INFO"; string name = item.Name; |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.2 ToString
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “ToString” API 함수는 Item 객체를  string 형태로 반환 합니다.

- API 함수 원형 ToString API함수의 원형은 다음과 같습니다.

| string ToString( void, ); |
| ------------------------- |

- 파라메터 ToString API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | -------- |
| void | 파라미터 없음. |

- 반환 값 string
- 사용법 및 주의사항

- 예제

| Item item = null; Api.getData("data://machine/channel/axis/machineposition", "machine=1&channel=1&axis=1-3", out item, false); string itemstr = item.ToString(); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.3 WriteTo
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “WriteTo” API 함수는 현재 item object 를 TextWriter 에 씁니다. abstract 함수.

- API 함수 원형 WriteTo API함수의 원형은 다음과 같습니다.

| void WriteTo( __IN TextWriter writer ); |
| --------------------------------------- |

- 파라메터 WriteTo API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | --------------------- |
| writer | 문자를 연속하여 쓸수 있는 추상 클래스 |

- 반환 값 void
- 사용법 및 주의사항

- 예제

| Item item1 = null; Api.getData("data://machine/channel/axis/machineposition", "machine=1&channel=1&axis=1-3", out item1, false); Item value = item1.find("value"); Item axisval = item1.find("filter"); string file = @"D:\hmi.txt"; using (TextWriter writer1 = File.CreateText(file)) { item1.WriteTo(writer1); } //hmi.txt 파일 내용 { "value": [ 104.96, 110, 160 ], "address": "data://machine/channel/axis/machineposition", "filter": "machine=1&channel=1&axis=1-3" } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.4 Find
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “Find” API 함수는 현재 item object에서 매개 변수와 동일한 항목의 값을 반환합니다.

- API 함수 원형 Find API함수의 원형은 다음과 같습니다.

| Item Find( __IN string name ); |
| ------------------------------ |

- 파라메터 Find API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------ |
| name | item 클래스에 있는 항목 이름 |

- 반환 값 매개 변수와 동일한 항목은 Item, Items, ItemArray로 반환.
- 사용법 및 주의사항

- 예제

| // value json 형식 : {"value": [104.96,110,160]} // axisval json 형식 : {"filter": "machine=1&channel=1&axis=1-3"} Item item = null; Api.getData('data://machine/channel/axis/machineposition", "machine=1&channel=1&axis=1-3", out item, false); Item value = item.find('value"); Item axisval = item.find("filter"); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.11.5 GetValueDouble ( GetArrayDouble )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “GetValueDouble 또는 GetArrayDouble” API 함수는 객체 이름에 해당하는 값을 double 또는 double[] 로 반환 합니다.

- API 함수 원형 GetValueDouble API함수의 원형은 다음과 같습니다.

| double GetValueDouble( __IN string name ); |
| ------------------------------------------ |

GetArrayDouble API함수의 원형은 다음과 같습니다.

| double[] GetArrayDouble( __IN string name ); |
| -------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------ |
| name | item 클래스에 있는 항목 이름 |

- 반환 값 double 또는 double[]
- 사용법 및 주의사항

- 예제

| // item json 형식 : {{"value": [104.96],"address": "data://machine/channel/axis/machineposition","filter": "machine=1&channel=1&axis=1"}} Item item = null; Api.getData('data://machine/channel/axis/machineposition", "machine=1&channel=1&axis=1", out item, false); double val = item.GetValueDouble("value"); // itemvals json 형식 : {{"value": [104.96,110,160],"address": "data://machine/channel/axis/machineposition","filter": "machine=1&channel=1&axis=1-3"}} Item itemvals = null; Api.getData("data://machine/channel/axis/machineposition", 'machine=1&channel=1&axis=1-3', out itemvals, false); double[] vals = itemvals.GetArrayDouble("value'); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.6 GetValueInt ( GetArrayInt )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “GetValueInt 또는 GetArrayInt” API 함수는 객체 이름에 해당하는 값을 int 또는 int[] 로 반환 합니다.

- API 함수 원형 GetValueInt API함수의 원형은 다음과 같습니다.

| int GetValueInt( __IN string name ); |
| ------------------------------------ |

GetArrayInt API함수의 원형은 다음과 같습니다.

| int[] GetArrayInt( __IN string name ); |
| -------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------ |
| name | item 클래스에 있는 항목 이름 |

- 반환 값 int 또는 int[]
- 사용법 및 주의사항

- 예제

| // item json 형식 : {{"value": [0],"address": "data://machine/plc/plcsignal","filter": "machine=1&type=0&count=1&start=X200.01&end=X200.01"}} Item item = null; Api.getPlcSignal(Api.CSCAM_PLC_TYPE.BIT, 1, "X200.01", out item, false); int val = item.GetValueInt(“value”); // itemvals json 형식 : {{"value": [0,0,0,0],"address": "data://machine/plc/plcsignal","filter": "machine=1&type=0&count=4&start=X200.01&end=X200.01"}} Item itemvals = null; Api.getPlcSignal(Api.CSCAM_PLC_TYPE.BIT, 4, "X200.01", out itemvals, false); int[] vals = itemvals.GetArrayInt(“value”); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.7 GetValueString ( GetArrayString )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “GetValueString 또는 GetArrayString” API 함수는 객체 이름에 해당하는 값을 string 또는 string[] 로 반환 합니다.

- API 함수 원형 GetValueString API함수의 원형은 다음과 같습니다.

| string GetValueString( __IN string name ); |
| ------------------------------------------ |

GetArrayString API함수의 원형은 다음과 같습니다.

| string[] GetArrayString( __IN string name ); |
| -------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------ |
| name | item 클래스에 있는 항목 이름 |

- 반환 값 string 또는 string[]
- 사용법 및 주의사항

- 예제

| // item json 형식 : {{"value": ["C://HX20_MC//NC//"],"address": "data://machine/channel/currentprogram/currentfile/programpath","filter": "machine=1&channel=1"}} Item item = null; Api.getData("data://machine/channel/currentProgram/currentFile/programPath", "machine=1&channel=1", out item, false); string val = item.GetValueString("value"); // itemval json 형식 : {{"value": [2],"address": "data://machine/channel/numberofalarms","filter": "machine=1&channel=1"}} Item itemval = null; Api.getData("data://machine/channel/numberofalarms", "machine=1&channel=1", out itemval, false); int alarmcount = itemval.GetValueInt("value"); // itemalarmtxt json 형식 : {{"value": ["비상정지중 입니다","MC READY 대기상태-MC READY 버튼을 눌러주세요."],"address": "data://machine/channel/alarm/alarmtext","filter": "machine=1&channel=1&alarm=1-2"}} string filter = "machine=1&channel=1&alarm=1-" + alarmcount.ToString(); Item itemalarmtxt = null; Api.getData("data://machine/channel/alarm/alarmtext", filter, ,out itemvals, false); string[] vals = itemvals.GetArrayString("value"); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.8 GetValueBoolean ( GetArrayBoolean )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “GetValueBoolean 또는 GetArrayBoolean” API 함수는 객체 이름에 해당하는 값을 Boolean 또는 Boolean[] 로 반환 합니다.

- API 함수 원형 GetValueBoolean API함수의 원형은 다음과 같습니다.

| Boolean GetValueBoolean( __IN string name ); |
| -------------------------------------------- |

GetArrayInt API함수의 원형은 다음과 같습니다.

| Boolean[] GetArrayBoolean( __IN string name ); |
| ---------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------ |
| name | item 클래스에 있는 항목 이름 |

- 반환 값 Boolean 또는 Boolean[]
- 사용법 및 주의사항

- 예제

| // item json 형식 : {{"value": [true],"address": "data://machine/nclinkstate","filter": "machine=1"}} Item item = null; int res = Api.getData("data://machine/nclinkstate", "machine=1", out item); Boolean val = item.GetValueBoolean(“value”); |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.9 MakeItem
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “MakeItem” API 함수는 객체 이름에 해당하는 값을 item 형식으로 반환합니다

- API 함수 원형 MakeItem API함수의 원형은 다음과 같습니다.

| Item MakeItem( __IN string name, __IN double value ); |
| ----------------------------------------------------- |

| Item MakeItem( __IN string name, __IN int value ); |
| -------------------------------------------------- |

| Item MakeItem( __IN string name, __IN string value ); |
| ----------------------------------------------------- |

| Item MakeItem( __IN string name, __IN Boolean value ); |
| ------------------------------------------------------ |

| Item MakeItem( __IN string name, __IN double[] value ); |
| ------------------------------------------------------- |

| Item MakeItem( __IN string name, __IN int[] value ); |
| ---------------------------------------------------- |

| Item MakeItem( __IN string name, __IN string[] value ); |
| ------------------------------------------------------- |

| Item MakeItem( __IN string name, __IN Boolean[] value ); |
| -------------------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----------------------- |
| name | item 클래스에 있는 항목 이름 |
| value | item 클래스에 있는 항목에 해당되는 값 |

- 반환 값 Item
- 사용법 및 주의사항

- 예제

| //item json 형식 : {{"value": [1,2,3,4,5,6,7,8,9]}} double[] data = { 1, 2, 3, 4, 5, 6, 7, 8, 9}; string addr = "data://machine/channel/workoffset/workoffsetvalue"; string filter = "channel=1&workoffset=1377"&workoffsetvalue=1-9" Item item = Item.MakeItem("value", data); Item res = null; try { Api.updateData(addr, filter, item, out res); } catch (Exception e) { MessageBox.Show(e.Message); } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.10 Items Class &amp; ItemArray Class
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “Items Class” 는  Item 객체의 배열 확장 Class인 ItemCollection 의 파생 Class. collection 구분자 : “ { “ , “ } “
"ItemArray Class” 는  Item 객체의 배열 확장 Class인 ItemCollection 의 파생 Class. collection 구분자 : “ [ “ , “ ] “
- 예제
" Appstatus.info " text 로 작성된 파일을 사용할 경우

| { "data": [ {"Name":"채널사용수량","Address":"data://machine/numberofchannels", “filter":""}, {"Name":"OperationMode","Address":"data://machine/operatemode", "filter":""}, {"Name":"채널사용여부","Address":"data://machine/channel/channelenabled","filter":"channel=1"} ] } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

코드 예제

| string fileData = File.ReadAllText("AppStatus.info", Encoding.Default); ItemTextParser parser = new ItemTextParser(); m_columnInfo = parser.Parse(fileData); Item data = m_columnInfo.find("data"); ItemArray dataArr = (ItemArray)data; foreach (Item item in dataArr) { try { string name = (string)item.find("name").GetValue(); string addr = (string)item.find("address").GetValue(); string filter = (string)item.find("filter").GetValue(); } Catch (Exception ex) { MessageBox.Show(ex.Message); } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.11.11 ItemCollection Class
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “ItemCollection Class” 는  Item 객체의 배열 확장 Class인 ItemCollection 의 파생 Class.

- API 함수

| 함수 이름 | 함수 원형 | 설명 |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| constructor | ItemCollection() ItemCollection(string name) Itemcollection(IEnumerable<Item> collection) Itemcollection(string name, IEnumerable<Item> collection) | |
| ToString | string ToString() | item class의 override 함수 Item 객체를 string 형태로 반환합니다 |
| WriteTo | void WriteTo(TextWriter writer) | item class의 override 함수 |
| GetValue | object GetValue() | List<item> 형식의 object 를 반환합니다. |
| IndexOf | Int indexOf(Item item) | Item 의 index 를 반환합니다. |
| Insert | void Insert(int index, Item item) | Item을 index 위치에 삽입합니다. |
| RemoveAt | void RemoveAt(int index) | Index 위치의 item 을 삭제합니다. |
| this[index] | Item this[int index] | Index 위치의 item을 반환하거나 index 위치에 저장합니다. |
| Add | void Add(Item item) | Item을 추가합니다. |
| Clear | void Clear() | collection의 item 을 전부 삭제 합니다. |
| Contains | bool Contains(Item item) | Collection에 item의 유무를 판단하여 bool 값으로 반환합니다. |
| CopyTo | void CopyTo(Item[] array, int arrayIndex) | Index 위치에 itemarray 를 copy 합니다. |
| Count | get 속성 | Collection 의 개수를 반환합니다. |
| IsReadOnly | get 속성 | false 값만 반환합니다. |
| Remove | bool Remove(Item item) | Collection 의 해당 item을 삭제합니다. |

---

##### 7.2.11.12 Parse ( ItemTextParser Class )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 “Parse” API 함수는 현재 ItemTextParser Class의 맴버 함수로 매개변수 text를 Parsing 하여 ItemString , ItemNumber, ItemBoolean 의 형태로 만든 후 최종 item class의 형태로 반환합니다.

- API 함수 원형 Parse API함수의 원형은 다음과 같습니다.

| Item Parse( __IN string text ); |
| ------------------------------- |

- 파라메터 Parse API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------- |
| text | Item 형으로 반환할 문자열 |

- 반환 값 Item
- 사용법 및 주의사항
Item Class에 맞게 text 를 입력해주어야 합니다.
- 예제

| Item json 형식 : { “control”: “app” } ItemTextParser parser = new ItemTextParser(); Item item = parser.Parse("{\"control\" : \"app\"}"); |
| -------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.11.13 Item 파생 클래스 ( ItemString, ItemNumber, ItemBoolean )
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.11 Item Class (C#) 

- API 함수 설명 Item 의 파생 클래스로 string Type 을 ItemString으로 , (int, double, float) Type 을 ItemNumber 로, bool Type 을 ItemBoolean 으로 반환하여 사용할 수 있습니다.

- API 함수 원형 ItemString API함수의 constructor 원형은 다음과 같습니다.

| ItemString ItemString( __IN string name. __IN string value ); |
| ------------------------------------------------------------- |

ItemNumber API함수의 constructor 원형은 다음과 같습니다.

| ItemNumber ItemNumber( __IN string name. __IN int value ( 또는 __IN double value 또는 __IN float value ) ); |
| ------------------------------------------------------------------------------------------------------- |

ItemBoolean API함수의 constructor 원형은 다음과 같습니다.

| ItemBooleamn ItemBoolean( __IN string name. __IN bool value ); |
| -------------------------------------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------------------------------------------------------------------------------------------ |
| name | item 클래스에 있는 항목 이름 |
| value | item 클래스에 있는 항목에 해당되는 값 Itemstring - string, ItemNumber - int, double. float, ItemBoolean - bool |

- 반환 값 ItemString. ItemNumber, ItemBoolean 으로 반환
- 사용법 및 주의사항
Item Class에 맞게 value 를 입력해주어야 합니다.
- 예제

| // Istr json 형식 : { "control": "app" } string str = "app"; ItemString istr = new ItemString("control", str); // Idb json 형식 : { "value": 6.02 } double db = 6.02; ItemNumber idb = new ItemNumber("value", db); // Ibool json 형식 : { "value": false } bool res = false; ItemBoolean ibool = new ItemBoolean("value", res); |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

#### 7.2.12 Item Class (C++)
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 

TORUS Platform에서 지원하는 C++용 Item Class에 대해 설명 합니다 . “Item” 클래스는 IntelligentAPI에서 제공되는 데이터 구조 클래스 입니다. 

---

##### 7.2.12.1 Constructor
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 Value 생성과 관련된 함수 입니다.
Value의 Type 을 변경하고자 할때 call SetXXX() 함수를 호출하거나 Overloaded 된 생성자를 사용할 수 있습니다.
- API 함수 원형 API함수의 원형은 다음과 같습니다.

| Value SetObject( // 빈 객체 생성시...// void ); |
| ----------------------------------------- |

| Value SetInt( __IN int value, ); |
| -------------------------------- |

| Value SetInt64( __IN int64_t value, ); |
| -------------------------------------- |

| Value SetUint( __IN unsigned int value, ); |
| ------------------------------------------ |

| Value SetUint64( __IN uint64_t value, ); |
| ---------------------------------------- |

| Value SetBool( __IN bool value, ); |
| ---------------------------------- |

| Value SetDouble( __IN double value, ); |
| -------------------------------------- |

| Value SetFloat( __IN float value, ); |
| ------------------------------------ |

| Value SetNull( // 빈 객체 생성시...// void ); |
| --------------------------------------- |

| Value SetArray( // 빈 객체 생성시...// void ); |
| ---------------------------------------- |

| Value SetString( __IN const char* value, __IN unsigned int len, ); |
| ------------------------------------------------------------------ |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------ |
| void | 파라미터 없음. |
| value | Value 에 넣을 값 |
| len | 문자열의 길이 |

- 반환 값 - 각 type별 Value 객체
- 사용법 및 주의사항

- 예제

| Api::Item item; item.SetObject(); Api::Value v; v.SetInt(10); // 또는 v = 10; Value b(true); // calls Value(bool) Value i(-123); // calls Value(int) Value u(123u); // calls Value(unsigned) Value d(1.5); // calls Value(double) Api::Value vs("test", 5); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| |

| //copy-string Api::Item document; Api::Value author; char buffer[10]; int len = sprintf_s(buffer, "%s %s", "Milo", "Yip"); // dynamically created string. author.SetString(buffer, len, document.GetAllocator()); memset(buffer, 0, sizeof(buffer)); //buffer 를 초기화 해도 author 의 value 는 유지됨. printf("author = %s, %d, %d\n", author.GetString(), len, author.GetStringLength()); |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| //const-string Api::Value s; s.SetString("rapidjson"); // can contain null character, length derived at compile time //s = "rapidjson"; // shortcut, same as above printf("s = %s, %d\n", s.GetString(), s.GetStringLength()); //character pointer 사용 예 const char* cstr = "rapidjson"; size_t cstr_len = strlen(cstr); // in case length is available Api::Value s1; // s.SetString(cstr); // will not compile s1.SetString(Api::StringRef(cstr)); // ok, assume safe lifetime, null-terminated //s1 = Api::StringRef(cstr); // shortcut, same as above printf("s1_first = %s, %d\n", s1.GetString(), s1.GetStringLength()); s1.SetString(Api::StringRef(cstr, cstr_len)); // faster, can contain null character //s1 = Api::StringRef(cstr, cstr_len); // shortcut, same as above printf("s1_second = %s, %d\n", s1.GetString(), s1.GetStringLength()); |

---

##### 7.2.12.2 Parse
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “Parse” API 함수는 JSON 형식으로 정의된 string (const char* a)을 Item 형식으로 분석합니다.

- API 함수 원형 Parse API함수의 원형은 다음과 같습니다.

| Item Parse( __IN const char* str ); |
| ----------------------------------- |

- 파라메터 Parse API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------ |
| str | 분석하고자 하는 문자열 |

- 반환 값 Item 로 반환.
- 사용법 및 주의사항 Parameter 의 경우 JSON 형식에 맞추어 주어야 합니다.

- 예제

| const char* str = "{\"hello\": \"world\",\"t\" : true,\"f\" : false,\"n\" : null,\"i\" : 123, \"pi\" : 3.1416,\"a\" : [1, 2, 3, 4]}"; Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

![image](./lib/NewItem469.png)

---

##### 7.2.12.3 HasMember
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “HasMember” API 함수는 item object에서 매개 변수와 동일한 항목의 값이 있는지를 반환합니다.

- API 함수 원형 HasMember API함수의 원형은 다음과 같습니다.

| bool HasMember( __IN const char* str ); |
| --------------------------------------- |

- 파라메터 HasMember API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------------ |
| str | 확인하고자 하는 문자열 |

- 반환 값 - true  :  동일한 항목이 있음.
- false  :  동일한 항목이 없음.
- 사용법 및 주의사항

- 예제

![image](./lib/NewItem470.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 assert(item.HasMember("hello")); |
| ------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.12.4 IsString/IsBool/IsNull/IsNumber/IsInt/IsDouble/IsArray
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “Is.....” API 함수는 item object 항목의 value 자료형을 확인하는 함수 입니다.

- API 함수 원형 IsString API함수의 원형은 다음과 같습니다.  string  여부를 확인 함수 입니다.

| bool IsString( void ); |
| ---------------------- |

IsBool API함수의 원형은 다음과 같습니다.  bool  여부를 확인 함수 입니다.

| bool IsBool( void ); |
| -------------------- |

IsNull API함수의 원형은 다음과 같습니다.  null  여부를 확인 함수 입니다.

| bool IsNull( void ); |
| -------------------- |

IsNumber API함수의 원형은 다음과 같습니다.  number  여부를 확인 함수 입니다.

| bool IsNumber( void ); |
| ---------------------- |

IsInt API함수의 원형은 다음과 같습니다.  int  여부를 확인 함수 입니다.

| bool IsInt( void ); |
| ------------------- |

IsDouble API함수의 원형은 다음과 같습니다.  double  여부를 확인 함수 입니다.

| bool IsDouble( void ); |
| ---------------------- |

IsArray API함수의 원형은 다음과 같습니다.  array  여부를 확인 함수 입니다.

| bool IsArray( void ); |
| --------------------- |

- 파라메터 Is... API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------- |
| void | 파라미터 없음 |

- 반환 값 - true  :  해당 자료형일 경우
- false  : 해당 자료형이 아닐 경우
- Querying Number 형식 참고

| Type | 설명 |
| -------- | -------------------------------------- |
| unsigned | 32-bit unsigned integer |
| int | 32-bit signed integer |
| uint64_t | 64-bit unsigned integer |
| int64_t | 64-bit signed integer |
| double | 64-bit double precision floating point |

- Number Check시 대상 유형 참고

| Checking | Obtaining |
| --------------- | -------------------- |
| bool IsNumber() | N/A |
| bool IsUint() | unsigned GetUint() |
| bool IsInt() | int GetInt() |
| bool IsUint64() | uint64_t GetUint64() |
| bool IsInt64() | int64_t GetInt64() |
| bool IsDouble() | double GetDouble() |

- 사용법 및 주의사항

- 예제

![image](./lib/NewItem471.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 assert(item.HasMember("hello")); assert(item["hello"].IsString()); printf("value = %s \n", item["hello"].IsString() ? "true" : "false"); // true assert(item["t"].IsBool()); printf("value = %s \n", item["t"].IsBool() ? "true" : "false"); //true assert(item["n"].IsNull()); printf("value = %s \n", item["n"].IsNull() ? "null" : "exist"); //true assert(item["i"].IsNumber()); printf("value = %s \n", item["i"].IsNumber() ? "true" : "false"); //true assert(item["i"].IsInt()); printf("value = %s \n", item["i"].IsInt() ? "true" : "false"); //true assert(item["pi"].IsNumber()); printf("value = %s \n", item["pi"].IsNumber() ? "true" : "false"); //true assert(item["pi"].IsDouble()); printf("value = %s \n", item["pi"].IsDouble() ? "true" : "false"); //true const Api::Value& a = item["a"]; assert(a.IsArray()); printf("value = %s \n", a.IsArray() ? "true" : "false"); //true |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.5 GetString/GetBool/GetInt/GetDouble
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “Get.....” API 함수는 item object 항목의 value 자료형의 값을 반환하는 함수 입니다.

- API 함수 원형 GetString API함수의 원형은 다음과 같습니다.

| const char* GetString( void ); |
| ------------------------------ |

GetBool API함수의 원형은 다음과 같습니다.

| bool GetBool( void ); |
| --------------------- |

GetInt API함수의 원형은 다음과 같습니다.

| int GetInt( void ); |
| ------------------- |

GetDouble API함수의 원형은 다음과 같습니다.

| double GetDouble( void ); |
| ------------------------- |

- 파라메터 Get... API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ------- |
| void | 파라미터 없음 |

- 반환 값 - 함수별 return 값

- 사용법 및 주의사항

- 예제

![image](./lib/NewItem472.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 assert(item.HasMember("hello")); assert(item["hello"].IsString()); printf("value = %s \n", item["hello"].GetString()); //world assert(item["t"].IsBool()); printf("value = %s \n", item["t"].GetBool() ? "true" : "false"); //true assert(item["i"].IsNumber()); assert(item["i"].IsInt()); printf("value = %d \n", item["i"].GetInt()); //123 assert(item["pi"].IsNumber()); assert(item["pi"].IsDouble()); printf("value = %g \n", item["pi"].GetDouble()); //3.1416 const Api::Value& a = item["a"]; assert(a.IsArray()); for (Api::SizeType i = 0; i < a.Size(); i++) printf("value a[%d] = %d \n", i, a[i].GetInt()); //1, 2, 3, 4 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.6 ConstValueIterator
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 설명 “ConstValueIterator” 는 item object 중  array형의  element의 value에 접근시 indices 를 사용하는 대신에 iterator 를 사용합니다.

- 사용법 및 주의사항

- 예제

![image](./lib/NewItem473.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 const Api::Value& a = item["a"]; assert(a.IsArray()); int count = 0; for (Api::Value::ConstValueIterator itr = a.Begin(); itr != a.End(); ++itr) printf("value a[%d] = %d \n", count++, itr->GetInt()); //1, 2, 3, 4 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.12.7 ConstMemberIterator
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 설명 “ConstMemberIterator” 는 item object의 모든 맴버에 접근시 iterator 를 사용합니다.

- 사용법 및 주의사항

- 예제

![image](./lib/NewItem474.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 static const char* kTypeNames[] = { "Null", "False", "True", "Object", "Array", "String", "Number" }; for (Api::Value::ConstMemberIterator itr = item.MemberBegin(); itr != item.MemberEnd(); ++itr) { printf("Type of member %s is %s\n", itr->name.GetString(), kTypeNames[itr->value.GetType()]); } |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.8 FindMember
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “FindMember” API 함수는 item object 항목의 특정 맴버에 접근 사용합니다.

- API 함수 원형 FindMember API함수의 원형은 다음과 같습니다.

| GenericMemberIterator FindMember( __IN const char* name ); |
| ---------------------------------------------------------- |

- 파라메터 FindMember API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ----- |
| name | 멤버 이름 |

- 반환 값
- 사용법 및 주의사항

- 예제

![image](./lib/NewItem475.png)

| Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 Api::Value::ConstMemberIterator itr = item.FindMember("hello"); if (itr != item.MemberEnd()) printf("%s\n", itr->value.GetString()); // world |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.9 AddMember
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “AddMember” API 함수는 item object 항목의 맴버를 추가하는 함수 입니다.

- API 함수 원형 AddMember API함수의 원형은 다음과 같습니다.

| Value AddMember( __IN const char* name, __IN Value& val, __IN MemoryPoolAllocator& alloc ); |
| ------------------------------------------------------------------------------------------- |

- 파라메터 AddMember API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------- |
| name | 멤버 이름 |
| val | Value 에 넣을 값 |
| alloc | item 의 allocator |

- 반환 값
- 사용법 및 주의사항

- 예제

| Api::Item item; item.SetObject(); Api::Value v; v.SetInt(10); Api::Value vs("test", 5); item.AddMember("aaa", v, item.GetAllocator()); item.AddMember("bbb", vs, item.GetAllocator()); Api::Value::ConstMemberIterator itr = item.FindMember("aaa"); if (itr != item.MemberEnd()) printf("%d\n", itr->value.GetInt()); Api::Value::ConstMemberIterator itr1 = item.FindMember("bbb"); if (itr1 != item.MemberEnd()) printf("%s - %d\n", itr1->value.GetString(), itr1->value.GetStringLength()); |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.12.10 Compare
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 Value 를 비교하고자 할때 "=="  와 "!=" 를 이용할 수 있습니다.

- 예제

![image](./lib/NewItem476.png)

| const char* str = "{\"hello\": \"world\",\"t\" : true,\"f\" : false,\"n\" : null,\"i\" : 123, \"pi\" : 3.1416,\"a\" : [1, 2, 3, 4]}"; Api::Item item; item.Parse(str); assert(item.IsObject()); // object 형태인지 확인 if (item["hello"] == item["n"]) // Compare values printf("Compare values is equal\n"); else printf("Compare values isn't equal\n"); // 출력 if (item["hello"] == "world")// Compare value with literal string printf("Compare string is equal\n"); //출력 else printf("Compare string isn't equal\n"); if (item["i"] != 123) // Compare with integers printf("Compare with integers isn't equal\n"); else printf("Compare with integers is equal\n"); //출력 if (item["pi"] != 3.14)// Compare with double. printf("Compare with double isn't equal\n"); //출 else printf("Compare with double is equal\n"); |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.11 Modify Array
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 Array 자료형의 경우 std::vector에서 제공되는 API 와 유사한 함수가 제공됩니다.

- API 함수

| 함수 이름 | 함수 원형 |
| -------- | ------------------------------------------------------------------------------------------------------------------ |
| Clear | Clear() |
| Reserve | Reserve(SizeType, Allocator&) |
| PushBack | Value& PushBack(Value&, Allocator&) template <typename T> GenericValue& PushBack(T, Allocator&) |
| PopBack | Value& PopBack() |
| Erase | ValueIterator Erase(ConstValueIterator pos) ValueIterator Erase(ConstValueIterator first, ConstValueIterator last) |

- 예제 ( PushBack )

| Api::Item item; item.SetObject(); Api::Value a(Api::kArrayType); Api::Item::AllocatorType& allocator = item.GetAllocator(); for (int i = 5; i <= 10; i++) a.PushBack(i, allocator); // allocator is needed for potential realloc(). // Fluent interface a.PushBack("Lua", allocator).PushBack("Mio", allocator); for (Api::Value::ConstMemberIterator itr = item.MemberBegin(); itr != item.MemberEnd(); ++itr) { printf("Type of member %s\n", itr->name.GetString()); } int count = 0; for (Api::Value::ConstValueIterator itr = a.Begin(); itr != a.End(); ++itr) { if (itr->IsInt()) printf("ConstValueIterator a[%d] = %d \n", count, itr->GetInt()); else if (itr->IsString()) printf("ConstValueIterator a[%d] = %s \n", count, itr->GetString()); count++; } ///console 결과 ConstValueIterator a[0] = 5 ConstValueIterator a[1] = 6 ConstValueIterator a[2] = 7 ConstValueIterator a[3] = 8 ConstValueIterator a[4] = 9 ConstValueIterator a[5] = 10 ConstValueIterator a[6] = Lua ConstValueIterator a[7] = Mio |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.12 Modify Object
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 Object를 편집하기 위해  member 를 추가하거나 제거하는 함수가 제공됩니다.

- API 함수

| 함수 이름 | 함수 원형 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AddMamber | Value& AddMember(Value&, Value&, Allocator& allocator) Value& AddMember(StringRefType, Value&, Allocator&) template <typename T> Value& AddMember(StringRefType, T value, Allocator&) |
| RemoveMember | bool RemoveMember(const char* name) bool RemoveMember(const Value& name) MemberIterator RemoveMember(MemberIterator) |
| EraseMember | MemberIterator EraseMember(MemberIterator) MemberIterator EraseMember(MemberIterator first, MemberIterator last) |

- 예제

| Api::Item item; item.SetObject(); Api::Value contact(Api::kObjectType); printf("AddMember ~~~~~~~~~~~~~~ \n"); contact.AddMember("name", "Milo", item.GetAllocator()); contact.AddMember("married", true, item.GetAllocator()); contact.AddMember(Api::Value("copy", item.GetAllocator()).Move(), Api::Value().Move(), item.GetAllocator()); Api::Value key("key", item.GetAllocator()); // copy string name Api::Value val(42); // some value contact.AddMember(key, val, item.GetAllocator()); for (Api::Value::ConstMemberIterator itr = contact.MemberBegin(); itr != contact.MemberEnd(); ++itr) { if (itr->value.IsInt()) printf("Name of member %s , value = %d\n", itr->name.GetString(), itr->value.GetInt()); else if (itr->value.IsBool()) printf("Name of member %s , value = %s\n", itr->name.GetString(), itr->value.GetBool() ? "true" : "false" ); else if (itr->value.IsString()) printf("Name of member %s , value = %s\n", itr->name.GetString(), itr->value.GetString()); else printf("Name of member %s , value type is none\n", itr->name.GetString()); } printf("Remove ~~~~~~~~~~~~~~ \n"); Api::Value::MemberIterator memi = contact.FindMember("copy"); contact.RemoveMember(memi); for (Api::Value::ConstMemberIterator itr = contact.MemberBegin(); itr != contact.MemberEnd(); ++itr) { if (itr->value.IsInt()) printf("Name of member %s , value = %d\n", itr->name.GetString(), itr->value.GetInt()); else if (itr->value.IsBool()) printf("Name of member %s , value = %s\n", itr->name.GetString(), itr->value.GetBool() ? "true" : "false" ); else if (itr->value.IsString()) printf("Name of member %s , value = %s\n", itr->name.GetString(), itr->value.GetString()); else printf("Name of member %s , value type is none\n", itr->name.GetString()); } ///console 결과 AddMember ~~~~~~~~~~~~~~ Name of member name , value = Milo Name of member married , value = true Name of member copy , value type is none Name of member key , value = 42 Remove ~~~~~~~~~~~~~~ Name of member name , value = Milo Name of member married , value = true Name of member key , value = 42 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

##### 7.2.12.13 Copy
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 “CopyFrom” API 함수는 item object에서 매개 변수를 copy 하고자 할때 제공되는 함수 입니다.

- API 함수 원형 CopyFrom API함수의 원형은 다음과 같습니다.

| Value& CopyFrom( __IN Value& member, __IN MemoryPoolAllocator& alloc, ); |
| ------------------------------------------------------------------------ |

- 파라메터 HasMember API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------- |
| member | item tree member |
| alloc | item 의 allocator |

- 반환 값
- 사용법 및 주의사항

- 예제

| Api::Item d; Api::Item::AllocatorType& a = d.GetAllocator(); Api::Value v1("foo"); //Api::Value v2(v1); // not allowed Api::Value v2(v1, a); // make a copy assert(v1.IsString()); // v1 untouched d.SetArray().PushBack(v1, a).PushBack(v2, a); assert(v1.IsNull() && v2.IsNull()); // both moved to d for (Api::Value::ConstValueIterator itr = d.Begin(); itr != d.End(); ++itr) { if (itr->IsString()) { printf("d member = %s \n", itr->GetString()); } } v2.CopyFrom(d, a); // copy whole document to v2 assert(d.IsArray() && d.Size() == 2); // d untouched for (Api::Value::ConstValueIterator itr = v2.Begin(); itr != v2.End(); ++itr) { if (itr->IsString()) printf("v2 member = %s \n", itr->GetString()); } v1.SetObject().AddMember("array", v2, a); const Api::Value& aa = v1["array"]; if (aa.IsArray()) { for (Api::SizeType i = 0; i < aa.Size(); i++) printf("v1 array member aa[%d] = %s \n", i, aa[i].GetString()); } d.PushBack(v1, a); printf("d member : "); for (Api::Value::ConstValueIterator itr = d.Begin(); itr != d.End(); ++itr) { if (itr->IsString()) { printf("%s, ", itr->GetString()); } else if (itr->IsObject()) { printf("array\n"); printf("array member : "); Api::Value::ConstMemberIterator itr1 = itr->FindMember("array"); if (itr1 != itr->MemberEnd()) { const Api::Value& bb = itr1->value; for (Api::SizeType i = 0; i < bb.Size(); i++) printf("%s, ", bb[i].GetString()); } } } |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

---

##### 7.2.12.14 Swap
7. TORUS Platform User API 7.2 TORUS Platform User API 설명 7.2.12 Item Class (C++) 

- API 함수 설명 "Swap" API 함수는 두 개의 item tree를 swapping 할수 있도록 제공된 함수 입니다.

- API 함수 원형 Swap API함수의 원형은 다음과 같습니다.

| Value& Swap( __IN Value& member, ); |
| ----------------------------------- |

- 파라메터 API 함수의 파라메터는 다음과 같습니다.

| Parameter 이름 | 설명 |
| ------------ | ---------------- |
| member | item tree member |

- 반환 값
- 사용법 및 주의사항

- 예제

| Api::Value a(123); Api::Value b("hello"); printf("a type is integal : %s , b type is string : %s\n", a.IsInt() ? "true" : "false", b.IsString() ? "true" : "false"); a.Swap(b); printf("after swap ~~~~~~~~~~~~~~ \n"); printf("a type is integal : %s , b type is string : %s\n", a.IsInt() ? "true" : "false", b.IsString() ? "true" : "false"); ///console 결과 a type is integal : true , b type is string : true after swap ~~~~~~~~~~~~~~ a type is integal : false , b type is string : false |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

---

## 8. TORUS Platform 에러코드 

---

### 8.1 User API 및 플랫폼 내부 모듈 오류 코드 
8. TORUS Platform 에러코드 

TORUS Platform의 User API와 플랫폼 내부 모듈의 오류코드에 대한 설명 입니다. 

---

#### 8.1.1 오류 코드 리스트
8. TORUS Platform 에러코드 8.1 User API 및 플랫폼 내부 모듈 오류 코드 

TORUS Platform의 User API 및 플랫폼 내부 모듈에서 발생하는 오류 코드는 다음과 같습니다.

| 분류 | 오류 코드(16진수) | 오류 코드(10진수) | 설명 |
| ---------- | ----------- | ---------------------------------------------- | --------------------------- |
| Manager | 0X2020500D | 538988557 | MgrCommunication 시뮬 버전 오류 |
| 0X20206003 | 538992643 | MgrCommunication 파라미터 Query 오류 | |
| 0X20206009 | 538992649 | MgrCommunication Address parsing 오류 | |
| 0X20206011 | 538992657 | MgrCommunication 유효하지 않은 updatedata의 data 오류 | |
| 0X20206012 | 538992658 | MgrCommunication 존재하지 않는 구독 오류 | |
| 0X20206013 | 538992659 | MgrCommunication 존재하지 않는 Timeseries 오류 | |
| 0X20206028 | 538992680 | MgrCommunication Address 또는 Filter 오류 | |
| 0X20207013 | 538996755 | StateModel 존재하지 않는 Timeseries 오류 | |
| 0X20102004 | 537927684 | MgrApplication AppInfo 로딩 오류 | |
| 0X20102005 | 537927685 | MgrApplication Filter Appname 표기 오류 | |
| 0X20102006 | 537927686 | MgrApplication Address에 AppName 속성이 존재하지 않는 오류 | |
| 0X20102007 | 537927687 | MgrApplication Address에 AppID 속성이 존재하지 않는 오류 | |
| 0X20102008 | 537927688 | MgrApplication App RpcClient 생성 오류 | |
| 0X20304009 | 540033033 | MgrCommand Address parsing 오류 | |
| 0X2030400A | 540033034 | MgrCommand 정의되지 않음 Address 공급자 오류 | |
| 0X20604009 | 543178761 | MgrLog Address parsing 오류 | |
| UserAPI | 0X20B00001 | 548405249 | Initialize 중복 시도 오류 |
| 0X20B00009 | 548405257 | Address parsing 오류 | |
| 0X20B00025 | 548405285 | Initialize 오류 | |
| 0X20B00028 | 548405288 | Address 또는 Filter 오류 | |
| 0X20B0002A | 548405290 | Address 결과값 Type 오류 | |
| 0X20B00032 | 548405298 | 알수 없는 구독 설정 오류 | |
| 0X20B00034 | 548405300 | Null Pointer 오류 | |
| Library | 0X20D00016 | 550502422 | LibAddress Split command 오류 |
| 0X20D00017 | 550502423 | LibAddress XAddress parsing 오류 | |
| 0X20D00018 | 550502424 | LibAddress Address Code 변환 오류 | |
| 0X20E00019 | 551551001 | LibAppinfo RpcClient Set 오류 | |
| 0X20E0001A | 551551002 | LibAppinfo App Info Set 오류 | |
| 0X20E0001B | 551551003 | LibAppinfo AppInfo Load 오류 | |
| 0X2150001C | 558891036 | LibRpcClient Connect 오류 | |
| 0X2150002F | 558891055 | LibRpcClient TimeOut 오류 | |
| 0X21500030 | 558891056 | LibRpcClient Canceled 오류 | |
| 0X21500031 | 558891057 | LibRpcClient Grpc 에서 알수 없는 오류 | |
| 0X21A00022 | 564133922 | LibSharedMap Platform Version 오류 | |
| 0X21A00023 | 564133923 | LibSharedMap Icon Name 오류 | |
| 0X21A00024 | 564133924 | LibSharedMap WatchDog Set 오류 | |
| 0X21A00025 | 564133925 | LibSharedMap Initialize 오류 | |
| 0X21A00026 | 564133926 | LibSharedMap Push Range 오류 | |
| 0X21A0002B | 564133931 | LibSharedMap Icon Path 오류 | |
| 0X21A0002C | 564133932 | LibSharedMap App Version 오류 | |
| 0X21A0002E | 564133934 | LibSharedMap App ProviderName 오류 | |

---

### 8.2 NC 통신 관련 오류 코드 
8. TORUS Platform 에러코드 

---

#### 8.2.1 오류 코드 리스트
8. TORUS Platform 에러코드 8.2 NC 통신 관련 오류 코드 

TORUS Platform의 NC 통신 부분에서 발생하는 오류 코드는 다음과 같습니다.

| 분류 | 에러 명 | 에러 코드 (10진수) | 에러 코드 (16진수) | 설명 |
| ----------------------------------- | ------------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| CNC 통신 | NC_ERR_DUPLICATED_WRITER | 565510144 | 0x21B50000 | 한번의 Write 명령에서 동일한 address와 동일한 filter값으로 두 번 이상 값을 쓰려고 할 때 발생 |
| NC_ERR_CONNET_FAIL | 565575680 | 0x21B60000 | NC와의 통신에 실패 | |
| NC_ERR_NO_MACHINE | 565579776 | 0x21B61000 | 접속할 NC정보가 없는데 접속을 시도한 경우 | |
| NC_ERR_NO_CONNET_TRY | 565583872 | 0x21B62000 | 접속 시도를 한적이 없는데 ReadWrite를 시도한 경우 | |
| NC_ERR_NO_FUNCTION | 565641216 | 0x21B70000 | 해당 NC에서는 지원하지 않는 기능 (지원하지만 구현되어 있지 않은 기능 포함) | |
| NC_ERR_NO_OPTION | 565706752 | 0x21B80000 | 해당 NC의 옵션에서는 지원하지 않는 기능 | |
| NC_ERR_NO_DLL | 565710848 | 0x21B81000 | 해당 기능에 필요한 DLL이 없는 경우 | |
| NC_ERR_NO_HANDLE | 565714944 | 0x21B82000 | 해당 NC와의 통신 중에 HANDLE에 문제가 발생한 경우 | |
| NC_ERR_NO_ACTIVE_TOOL_OR_TOOL_GROUP | 565719040 | 0x21B83000 | 활성화된 공구 혹은 공구 그룹이 없는 경우 | |
| NC_ERR_WRONG_TOOL_SYSTEM | 565723136 | 0x21B84000 | TOOL SYSTEM 설정이 실제와 맞지 않는 경우 | |
| NC_ERR_NO_TOOL_GROUP | 565727232 | 0x21B85000 | 해당 공구 그룹이 없는 경우 | |
| NC_ERR_NO_SELECETD_FILE | 565731328 | 0x21B86000 | 메인 혹은 서브 프로그램이 존재하지 않아서 정보를 읽어올수 없는 경우 | |
| NC_ERR_INVALID_WRITE_VALUE | 565772288 | 0x21B90000 | 허용되지 않는 WRITE값을 입력한 경우 | |
| NC_ERR_WRONG_WRITE_VALUE_LIST_COUNT | 565776384 | 0x21B91000 | 쓰기 값의 수량이 filter값에 입력된 수량과 다른 경우 | |
| NC_ERR_INAPPROPRIATE_STATUS | 565780480 | 0x21B92000 | 현재 상태에서는 불가능한 작업인 경우 | |
| NC_ERR_WRONG_FILTER_VALUE | 565837824 | 0x21BA0000 | 입력한 filter값 중 일부 혹은 전체가 잘못 되었음 | |
| NC_ERR_UNKNOWN | 565903360 | 0x21BB0000 | 알 수 없는 오류(주로 해당 Vendor의 오류값 중 해석되지 않은 오류) | |
| NC_ERR_NO_OBJECT_IN_NC | 565972992 | 0x21BC1000 | NC의 해당 경로에 해당 객체가 없는 경우 | |
| NC_ERR_NO_OBJECT_IN_LOCAL | 565973248 | 0x21BC1100 | LOCAL의 해당 경로에 해당 객체가 없는 경우 | |
| NC_ERR_WRONG_PATH_IN_NC | 565973504 | 0x21BC1200 | 파일 복사나 이동시 목적지(NC)의 경로가 없는 경로인 경우입니다. (복사나 이동 목적지 폴더가 존재하지 않는 경우) | |
| NC_ERR_WRONG_PATH_IN_LOCAL | 565973760 | 0x21BC1300 | 파일 복사나 이동시 목적지(LOCAL)의 경로가 없는 경로인 경우입니다. (복사나 이동 목적지 폴더가 존재하지 않는 경우) | |
| NC_ERR_OBJECT_AREADY_EXIST_IN_NC | 565977088 | 0x21BC2000 | NC의 해당 경로에 이미 같은 이름의 객체가 있는 경우 | |
| NC_ERR_OBJECT_AREADY_EXIST_IN_LOCAL | 565977344 | 0x21BC2100 | LOCAL의 해당 경로에 이미 같은 이름의 객체가 있는 경우 | |
| NC_ERR_FAIL_CREATE_OBJECT_IN_NC | 565981184 | 0x21BC3000 | NC의 해당 경로에 객체를 생성하는데 실패한 경우 | |
| NC_ERR_FAIL_CREATE_OBJECT_IN_LOCAL | 565981440 | 0x21BC3100 | LOCAL의 해당 경로에 객체를 생성하는데 실패한 경우 | |
| NC_ERR_OBJECT_IS_USED_IN_NC | 565985280 | 0x21BC4000 | NC의 해당 객체가 사용중인 경우 | |
| NC_ERR_OBJECT_IS_USED_IN_LOCAL | 565985536 | 0x21BC4100 | LOCAL의 해당 객체가 사용중인 경우 | |
| NC_ERR_STORAGE_SHORTAGE_IN_NC | 565989376 | 0x21BC5000 | NC의 용량이 부족한 경우 | |
| NC_ERR_WRONG_NC_FILE | 565993472 | 0x21BC6000 | NC 파일 내용이 형식에 맞지 않는 경우 | |
| NC_ERR_WRONG_NAME_OF_NC_FILE | 565993728 | 0x21BC6100 | NC 파일 이름 형식이 CNC 형식과 맞지 않는 경우 (KCNC의 경우 NC파일의 확장자가 ".nc"여야 합니다.) | |
| NC_ERR_FAIL_OPEN_OBJECT_IN_NC | 565997568 | 0x21BC7000 | NC의 해당 경로에 있는 파일을 열지 못한 경우 | |
| NC_ERR_FAIL_OPEN_OBJECT_IN_LOCAL | 565997824 | 0x21BC7100 | LOCAL의 해당 경로에 있는 파일을 열지 못한 경우 | |
| NC_ERR_WRONG_RETURN_DATA_TYPE | 566034432 | 0x21BD0000 | 반환 데이터가 MachineStateModel의 데이터 타입과 맞지 않는 경우 | |
| NC_ERR_NULL_VALUE | 566099968 | 0x21BE0000 | 해당 값이 NULL 값인 경우 | |
| NC_OK | 0 | 0x0 | 정상 | |
| NC 내부 PLC 데이터 통신 | - | 548438071 | 0x20b08037 | Memory mapping file 정보 읽기 실패 |
| CODE_ERROR_ADDRESS_OR_FILTER | 548442152 | 0x20b09028 | mapping table에 target Data type이 잘못 설정되어 있는 경우 | |
| CODE_ERROR_PARSING_ADDRES | 548442165 | 0x20b09035 | Memory mapping table에 없는 어드레스를 읽거나 쓰려고 할 때 | |
| CODE_ERROR_PARSING_FILTER | 548442166 | 0x20b09036 | Memory mapping table에 데이터 어드레스 범위 표기가 잘못되어 있거나 getData, updateData 함수 호출 시 입력하는 어드레스 필터 정보에 어드레스 범위가 잘못 지정되어 있는 경우 | |
| CODE_ERROR_MEM_MAP_FILE | 548442167 | 0x20b09037 | Memory mapping table의 NC internal PLC 측 데이터 어드레스 지정 부분에 잘못된 표기가 포함된 경우 | |
| CODE_ERROR_MEM_MAPPING | 548442168 | 0x20b09038 | Memory mapping table에 필수 설정해야 할 항목이 빠져 있는 경우 | |

---

### 8.3 비가공장비 통신 관련 오류 코드
8. TORUS Platform 에러코드 

---

#### 8.3.1 오류 코드 리스트
8. TORUS Platform 에러코드 8.3 비가공장비 통신 관련 오류 코드 

비 가공장비 통신 부분의 오류 코드에 대한 설명은 다음과 같습니다.

| 분류 | 오류 코드(10진수) | 오류 코드(16진수) | 설명 |
| ----------------------- | ----------- | --------------------------------------------- | ------------------------------- |
| 통신 Manager | 566235137 | 0x21C01001 | 요청한 데이터 어드레스에 필터가 지정되어 있지 않습니다. |
| 566235138 | 0x21C01002 | 요청한 데이터 어드레스에 "DIRECT" 플래그가 지정되어 있지 않습니다. | |
| 566235139 | 0x21C01003 | bit type 데이터 쓰기 지령 시, 오류 발생했습니다. | |
| 566235140 | 0x21C01004 | word type 데이터 쓰기 지령 시, 오류 발생했습니다. | |
| 566235141 | 0x21C01005 | 비 가공장비 통신 매니저 등록정보 파일에 오류가 있습니다. | |
| 566235142 | 0x21C01006 | 비 가공장비 통신 프로토콜 등록정보 파일에 오류가 있습니다. | |
| 566235147 | 0x21C0100B | 비 가공장비 리스트 파일이 없습니다. | |
| 566235148 | 0x21C0100C | 비 가공장비 리스트 파일 내에 잘못 기입된 정보가 있거나, 요소 정보가 없습니다. | |
| 566235149 | 0x21C0100D | 비 가공장비 리스트 파일 내에 Device ID가 중복되는 내용이 있습니다. | |
| 297799687 | 0x11C01007 | 저장된 로그가 없습니다. | |
| 297799689 | 0x11C01009 | 요청한 데이터 어드레스 내의 필터가 잘못되었습니다. | |
| 297799690 | 0x11C0100A | 쓰기 요청한 데이터의 타입 지정이 잘못 되었습니다. | |
| 297799688 | 0x11C01008 | 쓰기 지령에 사용한 데이터 어드레스에 필터가 지정되어 있지 않습니다. | |
| | | | |
| 통신 Library (MODBUS TCP) | 567287837 | 0x21D0201D | MODBUS TCP 통신 연결에 실패 했습니다. |
| 567287836 | 0x21D0201C | MODBUS TCP 통신 설정에 오류가 있습니다. | |
| 567287835 | 0x21D0201B | MODBUS TCP 통신 객체 생성에 실패했습니다. | |
| 567296021 | 0x21D04015 | 어드레스의 길이가 잘못되었습니다. | |
| 567287841 | 0x21D02021 | 알 수 없는 오류가 발생했습니다. TORUS Platform 웹사이트에 문의하세요 | |
| 567287810 | 0x21D02002 | MODBUS TCP 통신 객체가 존재하지 않습니다. | |
| 567287809 | 0x21D02001 | 장치에서 정보 읽기가 실패했습니다. | |
| 567287833 | 0x21D02019 | 장치의 읽기/쓰기 실패했습니다. | |
| 1104158723 | 0x41D02003 | MODBUS TCP 객체 소멸 시 오류가 발생했습니다. | |
| 1104158725 | 0x41D02005 | 메모리 해제에 실패했습니다. | |
| 567287834 | 0x21D0201A | 장치가 존재하지 않습니다. | |
| | | | |

