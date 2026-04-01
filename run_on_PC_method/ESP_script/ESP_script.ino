#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"
#include <sys/socket.h>

const char *ssid = "AI Sorter";

WiFiUDP udp;
const int udpPort = 4210;

struct Color {
    const char* name;
    int value;
};

Color colors[] = {
    {"no ball", 0},
    {"pink", 1},
    {"blue", 2},
    {"orange", 3},
    {"beige", 4}
};

unsigned long actionStarted = 0;

int diverterServoAngle;
int dispenseServoAngle;
int pinkAngle=0;
int blueAngle=45;
int orangeAngle=90;
int beigeAngle=180;
unsigned long sendTime = 0;

int currentPrediction;
int previousPrediction=0;

const int pwmChannelDispense = 0;
const int pwmChannelDiverter = 1;
const int pwmFreq = 50;
const int pwmResolution = 16;

const int minUs = 500;
const int maxUs = 2500;
int maxDuty = 65535;

//motor pin config
int dispenseServoPin = 13;
int diverterServoPin = 14;

// AI Thinker ESP32-CAM pin config
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

httpd_handle_t stream_httpd = NULL;

int getColorValue(const char* name);

static esp_err_t stream_handler(httpd_req_t *req);

void startCameraServer();

int usToDuty(int us);

void setServoAngle(int angle, int channel);

void releaseBall();

void setup() {
    Serial.begin(9600);

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    config.frame_size = FRAMESIZE_QVGA; // 320x240 (stable)
    config.jpeg_quality = 12;
    config.fb_count = 1;

    // Init camera
    if (esp_camera_init(&config) != ESP_OK) {
        Serial.println("Camera init failed");
        return;
    }

    // Connect WiFi
    WiFi.softAP(ssid);

    Serial.println("SoftAP started");
    Serial.print("IP address: ");
    Serial.println(WiFi.softAPIP());

    udp.begin(udpPort);
    Serial.printf("UDP server started on port %d\n", udpPort);

    startCameraServer();

    ledcAttachChannel(dispenseServoPin,50,16,pwmChannelDispense);

    ledcAttachChannel(diverterServoPin,50,16,pwmChannelDiverter);
    
}

void loop() {
   int packetSize = udp.parsePacket();
   unsigned long now = millis();
    if (packetSize) {
        char packet[128];
        int len = udp.read(packet, sizeof(packet) - 1);
        if (len > 0){
        packet[len] = 0;
        }
        Serial.printf("Received: %s\n", packet);

        currentPrediction = getColorValue(packet);
    }
    
    switch (currentPrediction){
        case 1:
            diverterServoAngle=pinkAngle;
            break;
        case 2:
            diverterServoAngle=blueAngle;
            break;
        case 3:
            diverterServoAngle=orangeAngle;
            break;
        case 4:
            diverterServoAngle=beigeAngle;
            break;
        default:
            break;
    }
    if(currentPrediction==previousPrediction && currentPrediction!=0){
        setServoAngle(diverterServoAngle,pwmChannelDiverter);
        actionStarted = millis();
    }
    if(now-actionStarted>500){
        releaseBall();
        actionStarted = 0;
    }
    previousPrediction=currentPrediction;
}

int getColorValue(const char* name) {
    for (int i = 0; i < sizeof(colors)/sizeof(colors[0]); i++) {
        if (strcmp(name, colors[i].name) == 0) {
            return colors[i].value;
        }
    }
    return -1;
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t* fb = NULL;
    esp_err_t res = ESP_OK;

    res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
    if (res != ESP_OK) return res;

    httpd_resp_send_chunk(req, "\r\n", 2);

    int client_sock = httpd_req_to_sockfd(req);

    while (true) {
        // Check if client disconnected
        char buf;
        int ret = recv(client_sock, &buf, 1, MSG_PEEK | MSG_DONTWAIT);
        if (ret == 0) { // client disconnected
            Serial.println("Client disconnected");
            break;
        } else if (ret < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            Serial.printf("Socket error: %d\n", errno);
            break;
        }

        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            break;
        }

        char header[128];
        int len = snprintf(header, sizeof(header),
                           "--frame\r\n"
                           "Content-Type: image/jpeg\r\n"
                           "Content-Length: %u\r\n\r\n",
                           fb->len);

        res = httpd_resp_send_chunk(req, header, len);
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        }

        esp_camera_fb_return(fb);

        if (res != ESP_OK) {
            Serial.println("Client disconnected during send");
            break;
        }
    }

    httpd_resp_send_chunk(req, NULL, 0);
    return ESP_OK;
}

void startCameraServer() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    httpd_uri_t stream_uri = {
        .uri       = "/stream",
        .method    = HTTP_GET,
        .handler   = stream_handler,
        .user_ctx  = NULL
    };
    

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}

int usToDuty(int us) {
  int periodUs = 1000000 / pwmFreq; // 20,000 µs
  return (us * maxDuty) / periodUs;
}

void setServoAngle(int angle, int channel) {
  int pulseWidth = map(angle, 0, 180, minUs, maxUs);
  int duty = usToDuty(pulseWidth);
  ledcWrite(channel, duty);
}

void releaseBall(){
    if(dispenseServoAngle==0){
        dispenseServoAngle=180;
    }
    else{
        dispenseServoAngle=0;
    }
    setServoAngle(dispenseServoAngle,pwmChannelDispense);

}
