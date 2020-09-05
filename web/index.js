// Copyright (c) 2020 Tulir Asokan
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
import { html, render, Component } from "https://unpkg.com/htm/preact/index.mjs?module"
import { Spinner } from "./spinner.js"
import { sendSticker } from "./widget-api.js"

// The base URL for fetching packs. The app will first fetch ${PACK_BASE_URL}/index.json,
// then ${PACK_BASE_URL}/${packFile} for each packFile in the packs object of the index.json file.
const PACKS_BASE_URL = "packs"
// This is updated from packs/index.json
let HOMESERVER_URL = "https://matrix-client.matrix.org"

const makeThumbnailURL = mxc => `${HOMESERVER_URL}/_matrix/media/r0/thumbnail/${mxc.substr(6)}?height=128&width=128&method=scale`

class App extends Component {
	constructor(props) {
		super(props)
		this.state = {
			packs: [],
			loading: true,
			error: null,
		}
		this.observer = null
	}

	observeIntersection = intersections => {
		for (const entry of intersections) {
			const img = entry.target.children.item(0)
			if (entry.isIntersecting) {
				img.setAttribute("src", img.getAttribute("data-src"))
				img.classList.add("visible")
			} else {
				img.removeAttribute("src")
				img.classList.remove("visible")
			}
		}
	}

	componentDidMount() {
		fetch(`${PACKS_BASE_URL}/index.json`).then(async indexRes => {
			if (indexRes.status >= 400) {
				this.setState({
					loading: false,
					error: indexRes.status !== 404 ? indexRes.statusText : null,
				})
				return
			}
			const indexData = await indexRes.json()
			HOMESERVER_URL = indexData.homeserver_url || HOMESERVER_URL
			// TODO only load pack metadata when scrolled into view?
			for (const packFile of indexData.packs) {
				const packRes = await fetch(`${PACKS_BASE_URL}/${packFile}`)
				const packData = await packRes.json()
				this.setState({
					packs: [...this.state.packs, packData],
					loading: false,
				})
			}
		}, error => this.setState({ loading: false, error }))
		this.observer = new IntersectionObserver(this.observeIntersection, {
			rootMargin: "100px",
			threshold: 0,
		})
	}

	componentDidUpdate() {
		for (const elem of document.getElementsByClassName("sticker")) {
			this.observer.observe(elem)
		}
	}

	componentWillUnmount() {
		this.observer.disconnect()
	}

	render() {
		if (this.state.loading) {
			return html`<div class="main spinner"><${Spinner} size=${80} green /></div>`
		} else if (this.state.error) {
			return html`<div class="main error">
				<h1>Failed to load packs</h1>
				<p>${this.state.error}</p>
			</div>`
		} else if (this.state.packs.length === 0) {
			return html`<div class="main empty"><h1>No packs found :(</h1></div>`
		}
		return html`<div class="main pack-list">
			${this.state.packs.map(pack => html`<${Pack} id=${pack.id} ...${pack}/>`)}
		</div>`
	}
}

const Pack = ({ title, stickers }) => html`<div class="stickerpack">
	<h1>${title}</h1>
	<div class="sticker-list">
		${stickers.map(sticker => html`
			<${Sticker} key=${sticker["net.maunium.telegram.sticker"].id} content=${sticker}/>
		`)}
	</div>
</div>`

const Sticker = ({ content }) => html`<div class="sticker" onClick=${() => sendSticker(content)}>
	<img data-src=${makeThumbnailURL(content.url)} alt=${content.body} />
</div>`

render(html`<${App} />`, document.body)
