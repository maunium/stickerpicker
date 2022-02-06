// maunium-stickerpicker - A fast and simple Matrix sticker picker widget.
// Copyright (C) 2020 Tulir Asokan
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
import { html, Component } from "../lib/htm/preact.js"
import { checkMobileSafari, checkAndroid } from "./user-agent-detect.js"

export function shouldDisplayAutofocusSearchBar() {
  return !checkMobileSafari() && !checkAndroid()
}

export function shouldAutofocusSearchBar() {
	return localStorage.mauAutofocusSearchBar === 'true' && shouldDisplayAutofocusSearchBar()
}

export function focusSearchBar() {
	const inputInWebView = document.querySelector('.search-box input')
	if (inputInWebView && shouldAutofocusSearchBar()) {
		inputInWebView.focus()
	}
}

export class SearchBox extends Component {
	constructor(props) {
		super(props)

		this.autofocus = shouldAutofocusSearchBar()
		this.value = props.value
		this.onSearch = props.onSearch
		this.onReset = props.onReset

		this.search = this.search.bind(this)
		this.clearSearch = this.clearSearch.bind(this)
	}

	componentDidMount() {
		focusSearchBar()
	}

	componentWillReceiveProps(props) {
		this.value = props.value
	}

	search(e) {
		if (e.key === "Escape") {
			this.clearSearch()
			return
		}
		this.onSearch(e.target.value)
	}

	clearSearch() {
		this.onReset()
	}

	render() {
		const isEmpty = !this.value

		const className = `icon-display ${isEmpty ? null : 'reset-click-zone'}`
		const title = isEmpty ? null : 'Click to reset'
		const onClick = isEmpty ? null : this.clearSearch
		const iconToDisplay = `icon-${isEmpty ? 'search' : 'reset'}`

		return html`
			<div class="search-box">
				<input
					placeholder="Find stickers …"
					value=${this.value}
					onKeyUp=${this.search}
					autoFocus=${this.autofocus}
				/>
				<div class=${className} title=${title} onClick=${onClick}>
					<span class="icon ${iconToDisplay}" />
				</div>
			</div>
		`
	}
}
