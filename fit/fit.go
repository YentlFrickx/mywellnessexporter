package fit

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"encoding/json"
	log "github.com/sirupsen/logrus"
	"github.com/tormoder/fit"
	"io/ioutil"
	"time"
)

type analyticsSample struct {
	T  int       `json:"t"`
	Vs []float64 `json:"vs"`
}

type hrSample struct {
	T  int     `json:"t"`
	Hr float64 `json:"hr"`
}

type mywellnessData struct {
	Data struct {
		Analytics struct {
			Samples []analyticsSample
			Hr      []hrSample
		} `json:"analitics"`
		EquipmentType string `json:"equipmentType"`
		Date          string `json:"date"`
		Data          []struct {
			RawValue float64
		}
	} `json:"data"`
}

func Convert(dataString string) {
	var sport fit.Sport

	var data mywellnessData
	json.Unmarshal([]byte(dataString), &data)

	if data.Data.EquipmentType == "Skillbike" {
		sport = fit.SportCycling
	} else if data.Data.EquipmentType == "Treadmill" {
		sport = fit.SportRunning
	} else {
		return
	}

	duration := data.Data.Data[0].RawValue * 60
	startDt := time.Now().Add(time.Second * time.Duration(duration))
	endDt := startDt.Add(time.Second * 10)

	h := fit.NewHeader(fit.V20, false)
	file, _ := fit.NewFile(fit.FileTypeActivity, h)
	act, _ := file.Activity()
	ev := fit.NewEventMsg()
	ev.Timestamp = startDt
	ev.Event = fit.EventTimer
	ev.EventType = fit.EventTypeStart
	act.Events = append(act.Events, ev)

	ev = fit.NewEventMsg()
	ev.Timestamp = endDt
	ev.Event = fit.EventTimer
	ev.EventType = fit.EventTypeStop
	act.Events = append(act.Events, ev)

	dataMsg := fit.NewRecordMsg()
	dataMsg.Distance = 20
	dataMsg.Timestamp = startDt
	dataMsg.ActivityType = fit.ActivityTypeRunning
	dataMsg.Altitude = 10
	act.Records = append(act.Records, dataMsg)

	session := fit.NewSessionMsg()
	session.Sport = sport
	session.Timestamp = endDt
	session.StartTime = startDt
	act.Sessions = append(act.Sessions, session)

	lap := fit.NewLapMsg()
	lap.Sport = sport
	lap.Timestamp = endDt
	lap.StartTime = startDt
	act.Laps = append(act.Laps, lap)

	outBuf := &bytes.Buffer{}

	err := fit.Encode(bufio.NewWriter(outBuf), file, binary.LittleEndian)

	if err != nil {
		log.Warnf("Error: %s", err.Error())
	}
	err = ioutil.WriteFile("output.fit", outBuf.Bytes(), 0644)

	if err != nil {
		log.Warnf("Error: %s", err.Error())
	}

}
