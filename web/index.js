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

// We need to detect iOS webkit because it has a bug related to scrolling non-fixed divs
const isMobileSafari = navigator.userAgent.match(/(iPod|iPhone|iPad)/) && navigator.userAgent.match(/AppleWebKit/)

class App extends Component {
	constructor(props) {
		super(props)
		this.state = {
			packs: [],
			loading: true,
			error: null,
		}
		this.imageObserver = null
		this.packListRef = null
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

		this.imageObserver = new IntersectionObserver(this.observeImageIntersections, {
			rootMargin: "100px",
		})
		this.sectionObserver = new IntersectionObserver(this.observeSectionIntersections)
	}

	observeImageIntersections(intersections) {
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

	observeSectionIntersections(intersections) {
		for (const entry of intersections) {
			const packID = entry.target.getAttribute("data-pack-id")
			const navElement = document.getElementById(`nav-${packID}`)
			if (entry.isIntersecting) {
				navElement.classList.add("visible")
			} else {
				navElement.classList.remove("visible")
			}
		}
	}

	componentDidUpdate() {
		for (const elem of this.packListRef.getElementsByClassName("sticker")) {
			this.imageObserver.observe(elem)
		}
		for (const elem of this.packListRef.children) {
			this.sectionObserver.observe(elem)
		}
	}

	componentWillUnmount() {
		this.imageObserver.disconnect()
		this.sectionObserver.disconnect()
	}

	render() {
		if (this.state.loading) {
			return html`<main class="spinner"><${Spinner} size=${80} green /></main>`
		} else if (this.state.error) {
			return html`<main class="error">
				<h1>Failed to load packs</h1>
				<p>${this.state.error}</p>
			</main>`
		} else if (this.state.packs.length === 0) {
			return html`<main class="empty"><h1>No packs found 😿</h1></main>`
		}
		return html`<main class="has-content">
			<nav>
				${this.state.packs.map(pack => html`<${NavBarItem} id=${pack.id} pack=${pack}/>`)}
			</nav>
			<div class="pack-list ${isMobileSafari ? "ios-safari-hack" : ""}" ref=${elem => this.packListRef = elem}>
				${this.state.packs.map(pack => html`<${Pack} id=${pack.id} pack=${pack}/>`)}
			</div>
		</main>`
	}
}

const NavBarItem = ({ pack }) => html`
	<a href="#pack-${pack.id}" id="nav-${pack.id}" data-pack-id=${pack.id} title=${pack.title}>
		<div class="sticker">
			<img src=${makeThumbnailURL(pack.stickers[0].url)}
				 alt=${pack.stickers[0].body} class="visible" />
		</div>
	</a>
`

const Pack = ({ pack }) => html`
	<section class="stickerpack" id="pack-${pack.id}" data-pack-id=${pack.id}>
		<h1>${pack.title}</h1>
		<div class="sticker-list">
			${pack.stickers.map(sticker => html`
				<${Sticker} key=${sticker["net.maunium.telegram.sticker"].id} content=${sticker}/>
			`)}
		</div>
	</section>
`

const Sticker = ({ content }) => html`
	<div class="sticker" onClick=${() => sendSticker(content)}>
		<img data-src=${makeThumbnailURL(content.url)} alt=${content.body} />
	</div>
`

render(html`<${App} />`, document.body)
