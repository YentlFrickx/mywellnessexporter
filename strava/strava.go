package strava

import (
	"bytes"
	"encoding/json"
	log "github.com/sirupsen/logrus"
	"io"
	"net/http"
	"os"
)

type Strava struct {
	stravaId           string
	stravaRefreshToken string
	stravaClientId     string
	stravaClientSecret string
	accessToken        string
}

func getStrava() Strava {
	stravaId := os.Getenv("STRAVA_ID")
	stravaClientId := os.Getenv("STRAVA_CLIENT_ID")
	stravaClientSecret := os.Getenv("STRAVA_CLIENT_SECRET")
	stravaRefreshToken := os.Getenv("STRAVA_REFRESH_TOKEN")

	return Strava{
		stravaId:           stravaId,
		stravaRefreshToken: stravaRefreshToken,
		stravaClientId:     stravaClientId,
		stravaClientSecret: stravaClientSecret,
	}
}

type RefreshData struct {
	GrantType    string `json:"grant_type"`
	ClientId     string `json:"client_id"`
	ClientSecret string `json:"client_secret"`
	RefreshToken string `json:"refresh_token"`
}

type RefreshResponse struct {
	AccessToken string `json:"access_token"`
}

func (s Strava) refreshToken() bool {
	data := RefreshData{
		GrantType:    "refresh_token",
		ClientId:     s.stravaClientId,
		ClientSecret: s.stravaClientSecret,
		RefreshToken: s.stravaRefreshToken,
	}
	body, _ := json.Marshal(data)
	request, err := http.NewRequest("POST", "https://www.strava.com/api/v3/oauth/token", bytes.NewBuffer(body))
	request.Header.Set("Content-Type", "application/json; charset=UTF-8")

	client := &http.Client{}
	resp, err := client.Do(request)
	if err != nil {
		log.WithError(err)
		return false
	}

	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		log.Printf("response Body: %s", string(body))
		return false
	}

	var refreshResponse RefreshResponse

	err = json.NewDecoder(resp.Body).Decode(&refreshResponse)
	if err != nil {
		log.WithError(err)
		return false
	}
	s.accessToken = refreshResponse.AccessToken

	return true
}
