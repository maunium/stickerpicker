// Copyright (c) 2020 Tulir Asokan
//
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.
import { html, render, Component } from "../lib/htm/preact.js"
import { Spinner } from "./spinner.js"
import * as widgetAPI from "./widget-api.js"
import * as frequent from "./frequently-used.js"

// The base URL for fetching packs. The app will first fetch ${PACK_BASE_URL}/index.json,
// then ${PACK_BASE_URL}/${packFile} for each packFile in the packs object of the index.json file.
const PACKS_BASE_URL = "packs"
// This is updated from packs/index.json
let HOMESERVER_URL = "https://matrix-client.matrix.org"

const makeThumbnailURL = mxc => `${HOMESERVER_URL}/_matrix/media/r0/thumbnail/${mxc.substr(6)}?height=128&width=128&method=scale`

// We need to detect iOS webkit because it has a bug related to scrolling non-fixed divs
// This is also used to fix scrolling to sections on Element iOS
const isMobileSafari = navigator.userAgent.match(/(iPod|iPhone|iPad)/) && navigator.userAgent.match(/AppleWebKit/)

class App extends Component {
	constructor(props) {
		super(props)
		this.state = {
			packs: [],
			loading: true,
			error: null,
			stickersPerRow: parseInt(localStorage.mauStickersPerRow || "4"),
			frequentlyUsed: {
				id: "frequently-used",
				title: "Frequently used",
				stickerIDs: frequent.get(),
				stickers: [],
			},
		}
		this.stickersByID = new Map(JSON.parse(localStorage.mauFrequentlyUsedStickerCache || "[]"))
		this.state.frequentlyUsed.stickers = this._getStickersByID(this.state.frequentlyUsed.stickerIDs)
		this.imageObserver = null
		this.packListRef = null
		this.navRef = null
		this.sendSticker = this.sendSticker.bind(this)
		this.navScroll = this.navScroll.bind(this)
		this.reloadPacks = this.reloadPacks.bind(this)
		this.observeSectionIntersections = this.observeSectionIntersections.bind(this)
		this.observeImageIntersections = this.observeImageIntersections.bind(this)
	}

	_getStickersByID(ids) {
		return ids.map(id => this.stickersByID.get(id)).filter(sticker => !!sticker)
	}

	updateFrequentlyUsed() {
		const stickerIDs = frequent.get()
		const stickers = this._getStickersByID(stickerIDs)
		this.setState({
			frequentlyUsed: {
				...this.state.frequentlyUsed,
				stickerIDs,
				stickers,
			},
		})
		localStorage.mauFrequentlyUsedStickerCache = JSON.stringify(stickers.map(sticker => [sticker.id, sticker]))
	}

	setStickersPerRow(val) {
		localStorage.mauStickersPerRow = val
		document.documentElement.style.setProperty("--stickers-per-row", localStorage.mauStickersPerRow)
		this.setState({
			stickersPerRow: val,
		})
		this.packListRef.scrollTop = this.packListRef.scrollHeight
	}

	reloadPacks() {
		this.imageObserver.disconnect()
		this.sectionObserver.disconnect()
		this.setState({ packs: [] })
		this._loadPacks(true)
	}

	_loadPacks(disableCache = false) {
		const cache = disableCache ? "no-cache" : undefined
		fetch(`${PACKS_BASE_URL}/index.json`, { cache }).then(async indexRes => {
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
				const packRes = await fetch(`${PACKS_BASE_URL}/${packFile}`, { cache })
				const packData = await packRes.json()
				for (const sticker of packData.stickers) {
					this.stickersByID.set(sticker.id, sticker)
				}
				this.setState({
					packs: [...this.state.packs, packData],
					loading: false,
				})
			}
			this.updateFrequentlyUsed()
		}, error => this.setState({ loading: false, error }))
	}

	componentDidMount() {
		document.documentElement.style.setProperty("--stickers-per-row", this.state.stickersPerRow.toString())
		this._loadPacks()
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
		const navWidth = this.navRef.getBoundingClientRect().width
		let minX = 0, maxX = navWidth
		let minXElem = null
		let maxXElem = null
		for (const entry of intersections) {
			const packID = entry.target.getAttribute("data-pack-id")
			const navElement = document.getElementById(`nav-${packID}`)
			if (entry.isIntersecting) {
				navElement.classList.add("visible")
				const bb = navElement.getBoundingClientRect()
				if (bb.x < minX) {
					minX = bb.x
					minXElem = navElement
				} else if (bb.right > maxX) {
					maxX = bb.right
					maxXElem = navElement
				}
			} else {
				navElement.classList.remove("visible")
			}
		}
		if (minXElem !== null) {
			minXElem.scrollIntoView({ inline: "start" })
		} else if (maxXElem !== null) {
			maxXElem.scrollIntoView({ inline: "end" })
		}
	}

	componentDidUpdate() {
		if (this.packListRef === null) {
			return
		}
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

	sendSticker(evt) {
		const id = evt.currentTarget.getAttribute("data-sticker-id")
		const sticker = this.stickersByID.get(id)
		frequent.add(id)
		this.updateFrequentlyUsed()
		widgetAPI.sendSticker(sticker)
	}

	navScroll(evt) {
		this.navRef.scrollLeft += evt.deltaY * 12
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
			<nav onWheel=${this.navScroll} ref=${elem => this.navRef = elem}>
				<${NavBarItem} pack=${this.state.frequentlyUsed} iconOverride="res/recent.svg" altOverride="🕓️" />
				${this.state.packs.map(pack => html`<${NavBarItem} id=${pack.id} pack=${pack}/>`)}
				<${NavBarItem} pack=${{ id: "settings", title: "Settings" }} iconOverride="res/settings.svg" altOverride="⚙️️" />
			</nav>
			<div class="pack-list ${isMobileSafari ? "ios-safari-hack" : ""}" ref=${elem => this.packListRef = elem}>
				<${Pack} pack=${this.state.frequentlyUsed} send=${this.sendSticker} />
				${this.state.packs.map(pack => html`<${Pack} id=${pack.id} pack=${pack} send=${this.sendSticker} />`)}
				<${Settings} app=${this}/>
			</div>
		</main>`
	}
}

const Settings = ({ app }) => html`
	<section class="stickerpack settings" id="pack-settings" data-pack-id="settings">
		<h1>Settings</h1>
		<div class="settings-list">
			<button onClick=${app.reloadPacks}>Reload</button>
			<div>
				<label for="stickers-per-row">Stickers per row: ${app.state.stickersPerRow}</label>
				<input type="range" min=2 max=10 id="stickers-per-row" id="stickers-per-row"
					value=${app.state.stickersPerRow}
					onInput=${evt => app.setStickersPerRow(evt.target.value)} />
			</div>
		</div>
	</section>
`

// By default we just let the browser handle scrolling to sections, but webviews on Element iOS
// open the link in the browser instead of just scrolling there, so we need to scroll manually:
const scrollToSection = (evt, id) => {
	const pack = document.getElementById(`pack-${id}`)
	pack.scrollIntoView({ block: "start", behavior: "instant" })
	evt.preventDefault()
}

const NavBarItem = ({ pack, iconOverride = null, altOverride = null }) => html`
	<a href="#pack-${pack.id}" id="nav-${pack.id}" data-pack-id=${pack.id} title=${pack.title}
	   onClick=${isMobileSafari ? (evt => scrollToSection(evt, pack.id)) : undefined}>
		<div class="sticker ${iconOverride ? "icon" : ""}">
			${iconOverride ? html`
				<img src=${iconOverride} alt=${altOverride} class="visible"/>
			` : html`
				<img src=${makeThumbnailURL(pack.stickers[0].url)}
					alt=${pack.stickers[0].body} class="visible" />
			`}
		</div>
	</a>
`

const Pack = ({ pack, send }) => html`
	<section class="stickerpack" id="pack-${pack.id}" data-pack-id=${pack.id}>
		<h1>${pack.title}</h1>
		<div class="sticker-list">
			${pack.stickers.map(sticker => html`
				<${Sticker} key=${sticker.id} content=${sticker} send=${send}/>
			`)}
		</div>
	</section>
`

const Sticker = ({ content, send }) => html`
	<div class="sticker" onClick=${send} data-sticker-id=${content.id}>
		<img data-src=${makeThumbnailURL(content.url)} alt=${content.body} />
	</div>
`

render(html`<${App} />`, document.body)
