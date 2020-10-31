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
import { html } from "../lib/htm/preact.js"

const Button = ({
    type = "button", class: className = "", children,
    variant = "filled", size = "normal",
    ...customProps
}) => {
    const props = {
        class: `mau-button variant-${variant} size-${size} ${className}`,
        type, ...customProps,
    }
    return html`<button ...${props}>${children}</button>`
}

export default Button
