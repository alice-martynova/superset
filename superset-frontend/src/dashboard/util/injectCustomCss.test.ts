/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import injectCustomCss from './injectCustomCss';

describe('injectCustomCss', () => {
  afterEach(() => {
    document.querySelectorAll('.CssEditor-css').forEach(node => node.remove());
  });

  test('injects the provided CSS into a <style> tag in the document head', () => {
    const remove = injectCustomCss('.foo { color: red; }');
    const styleEl = document.head.querySelector(
      'style.CssEditor-css',
    ) as HTMLStyleElement | null;
    expect(styleEl).not.toBeNull();
    expect(styleEl!.textContent).toBe('.foo { color: red; }');
    remove();
    expect(document.head.querySelector('style.CssEditor-css')).toBeNull();
  });

  test('does not parse injected content as HTML (no script element created)', () => {
    const payload = '</style><script>window.__xssTriggered = true;</script>';
    const remove = injectCustomCss(payload);
    const styleEl = document.head.querySelector(
      'style.CssEditor-css',
    ) as HTMLStyleElement | null;
    expect(styleEl).not.toBeNull();
    // textContent must contain the raw payload as text, not as parsed HTML.
    expect(styleEl!.textContent).toBe(payload);
    // No <script> element should have been produced inside the <style> tag.
    expect(styleEl!.querySelector('script')).toBeNull();
    remove();
  });
});
