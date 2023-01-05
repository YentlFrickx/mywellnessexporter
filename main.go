package main

import (
	"io/ioutil"
	"mywellnessexporter/fit"
)

func main() {

	b, err := ioutil.ReadFile("Details.json")
	if err != nil {
		panic(err)
	}

	fit.Convert(string(b))
}
