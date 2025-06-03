import { startEvernotePluginServer } from '../src/index'

describe('startEvernotePluginServer', () => {
  it('runs without throwing', () => {
    expect(startEvernotePluginServer).not.toThrow()
  })
})