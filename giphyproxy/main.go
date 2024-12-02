// maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
// Copyright (C) 2024 Tulir Asokan
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"regexp"
	"time"

	"go.mau.fi/util/exerrors"
	"gopkg.in/yaml.v3"
	"maunium.net/go/mautrix/federation"
	"maunium.net/go/mautrix/mediaproxy"
)

type Config struct {
	mediaproxy.BasicConfig  `yaml:",inline"`
	mediaproxy.ServerConfig `yaml:",inline"`
	Destination             string `yaml:"destination"`
}

var configPath = flag.String("config", "config.yaml", "config file path")
var generateServerKey = flag.Bool("generate-key", false, "generate a new server key and exit")

var giphyIDRegex = regexp.MustCompile(`^[a-zA-Z0-9-_]+$`)
var destination = "https://i.giphy.com/%s.webp"

func main() {
	flag.Parse()
	if *generateServerKey {
		fmt.Println(federation.GenerateSigningKey().SynapseString())
	} else {
		cfgFile := exerrors.Must(os.ReadFile(*configPath))
		var cfg Config
		exerrors.PanicIfNotNil(yaml.Unmarshal(cfgFile, &cfg))
		mp := exerrors.Must(mediaproxy.NewFromConfig(cfg.BasicConfig, getMedia))
		mp.KeyServer.Version.Name = "maunium-stickerpicker giphy proxy"
		mp.ForceProxyLegacyFederation = true
		if cfg.Destination != "" {
			destination = cfg.Destination
		}
		exerrors.PanicIfNotNil(mp.Listen(cfg.ServerConfig))
	}
}

func getMedia(_ context.Context, id string, _ map[string]string) (response mediaproxy.GetMediaResponse, err error) {
	// This is not related to giphy, but random cats are always fun
	if id == "cat" {
		return &mediaproxy.GetMediaResponseURL{
			URL:       "https://cataas.com/cat",
			ExpiresAt: time.Now(),
		}, nil
	}
	if !giphyIDRegex.MatchString(id) {
		return nil, mediaproxy.ErrInvalidMediaIDSyntax
	}
	return &mediaproxy.GetMediaResponseURL{
		URL: fmt.Sprintf(destination, id),
	}, nil
}
