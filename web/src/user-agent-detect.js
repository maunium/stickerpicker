export const getUserAgent = () => navigator.userAgent || navigator.vendor || window.opera

export const checkiOSDevice = () => {
  const agent = getUserAgent()
  return agent.match(/(iPod|iPhone|iPad)/)
}

export const checkMobileSafari = () => {
  const agent = getUserAgent()
  return agent.match(/(iPod|iPhone|iPad)/) && agent.match(/AppleWebKit/)
}

export const checkAndroid = () => {
  const agent = getUserAgent()
  return agent.match(/android/i)
}

export const checkMobileDevice = () => checkiOSDevice() || checkAndroid()
